"""
Stage 7, 8.5 & 9: Intelligent Conversational Financial Assistant API Router
Provides authenticated endpoints for:
- POST /api/v1/assistant/chat: Multi-turn conversational chatbot with persistent memory.
- GET /api/v1/assistant/conversations: List user's conversation threads.
- GET /api/v1/assistant/conversations/{id}: Retrieve full message history of a conversation.
- PATCH /api/v1/assistant/conversations/{id}: Rename a conversation title.
- DELETE /api/v1/assistant/conversations/{id}: Delete a conversation and message history.
- POST /api/v1/assistant/query: Backwards-compatible evidence-grounded Q&A.
- GET /api/v1/assistant/suggestions: Starter prompts tailored to account type and data sufficiency.
- GET /api/v1/assistant/provider-status: AI provider and hybrid engine status.
"""
import re
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.conversation import Conversation, ChatMessage, generate_conversation_id
from app.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    AssistantSuggestionsResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatConversationSummary,
    ChatConversationDetail,
    ChatMessageItem,
    ConversationRenameRequest,
    ChatAction,
)
from app.services.auth_service import get_current_user
from app.services.financial_assistant_engine import FinancialAssistantEngine
from app.services.business_service import (
    get_active_business,
    get_environment_subscriptions,
    get_environment_transactions,
)

router = APIRouter(prefix="/assistant", tags=["Financial Assistant"])


def _generate_title_from_prompt(prompt: str) -> str:
    cleaned = prompt.strip().replace("\n", " ")
    cleaned = re.sub(r"^(can you|please|what is|tell me|show me)\s+", "", cleaned, flags=re.IGNORECASE).strip()
    if not cleaned:
        return "Financial Inquiry"
    title = cleaned[:45].strip()
    if len(prompt.strip()) > 45:
        title += "..."
    return title[0].upper() + title[1:] if len(title) > 1 else title.upper()


# ---------------------------------------------------------------------------
# Conversational Chatbot Endpoints (Phase 9)
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatMessageResponse)
def chat_financial_assistant(
    request: ChatMessageRequest,
    http_request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits a conversational message to SubWise AI Assistant.
    Maintains persistent multi-turn chat history in PostgreSQL.
    Grounds all responses in ledger actuals, subscriptions, and forecast simulations.
    Provides interactive action cards and deep links.
    """
    biz = get_active_business(current_user=current_user, db=db, request=http_request)
    subscriptions = get_environment_subscriptions(db=db, biz=biz, request=http_request)
    transactions = get_environment_transactions(db=db, biz=biz, request=http_request)

    # 1. Resolve or create conversation thread with strict user isolation
    conv = None
    if request.conversation_id:
        conv = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )

    if not conv:
        conv = Conversation(
            id=generate_conversation_id(),
            user_id=current_user.id,
            business_id=biz.id,
            account_type=biz.account_type or "business",
            title=_generate_title_from_prompt(request.message),
        )
        db.add(conv)
        db.flush()

    # 2. Record User Message
    user_msg = ChatMessage(
        conversation_id=conv.id,
        role="user",
        content=request.message,
        meta_data={"context_hint": request.context_hint},
    )
    db.add(user_msg)
    db.flush()

    # 3. Fetch recent history for multi-turn conversational grounding
    recent_db_msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(10)
        .all()
    )
    history_payload = [
        {"role": m.role, "content": m.content}
        for m in recent_db_msgs
    ]

    # 4. Generate grounded financial response
    query_req = AssistantQueryRequest(
        message=request.message,
        conversation_id=conv.id,
        context_hint=request.context_hint,
    )
    engine_res: AssistantQueryResponse = FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=subscriptions,
        transactions=transactions,
        request=query_req,
        db=db,
        history=history_payload,
    )

    # 5. Extract metadata & actions
    provider = "gemini" if engine_res.is_ai_generated else "deterministic"
    actions_dicts = [a.model_dump() for a in (engine_res.actions or [])]
    cards_dicts = [c.model_dump() for c in (engine_res.evidence_cards or [])]

    # 6. Record Assistant Message in DB
    assistant_msg = ChatMessage(
        conversation_id=conv.id,
        role="assistant",
        content=engine_res.response_text,
        meta_data={
            "provider": provider,
            "is_ai_generated": engine_res.is_ai_generated,
            "generation_model": engine_res.generation_model,
            "intent": engine_res.intent,
            "data_sufficiency_status": engine_res.data_sufficiency_status,
            "evidence_cards": cards_dicts,
            "suggested_followups": engine_res.suggested_followups,
            "actions": actions_dicts,
            "reporting_period": engine_res.reporting_period,
            "disclaimer": engine_res.disclaimer,
        },
    )
    db.add(assistant_msg)

    # 7. Update conversation timestamp
    conv.updated_at = datetime.datetime.utcnow()
    db.commit()

    return ChatMessageResponse(
        conversation_id=conv.id,
        title=conv.title,
        message=engine_res.response_text,
        provider=provider,
        is_ai_generated=engine_res.is_ai_generated,
        generation_model=engine_res.generation_model,
        intent=engine_res.intent,
        data_sufficiency_status=engine_res.data_sufficiency_status,
        evidence_cards=engine_res.evidence_cards,
        suggested_followups=engine_res.suggested_followups,
        actions=engine_res.actions,
        disclaimer=engine_res.disclaimer,
        reporting_period=engine_res.reporting_period,
        created_at=assistant_msg.created_at.isoformat() if assistant_msg.created_at else None,
    )


@router.get("/conversations", response_model=List[ChatConversationSummary])
def list_conversations(
    http_request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns list of all active conversation threads for the current user.
    Strict tenant and user-level isolation.
    """
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    summaries = []
    for c in convs:
        msgs = c.messages or []
        last_msg = msgs[-1].content if msgs else None
        if last_msg and len(last_msg) > 90:
            last_msg = last_msg[:90] + "..."
        summaries.append(
            ChatConversationSummary(
                id=c.id,
                title=c.title,
                account_type=c.account_type,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=len(msgs),
                last_message=last_msg,
            )
        )
    return summaries


@router.get("/conversations/{conversation_id}", response_model=ChatConversationDetail)
def get_conversation_detail(
    conversation_id: str,
    http_request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns full message history and metadata for a specific conversation.
    Strictly isolated by current_user.id.
    """
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation thread not found.")

    msg_items = [
        ChatMessageItem(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            meta_data=m.meta_data,
            created_at=m.created_at,
        )
        for m in (conv.messages or [])
    ]

    return ChatConversationDetail(
        id=conv.id,
        title=conv.title,
        account_type=conv.account_type,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=msg_items,
    )


@router.patch("/conversations/{conversation_id}")
def rename_conversation(
    conversation_id: str,
    payload: ConversationRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Renames a conversation thread title.
    """
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation thread not found.")

    conv.title = payload.title.strip()
    conv.updated_at = datetime.datetime.utcnow()
    db.commit()

    return {"detail": "Conversation renamed successfully", "id": conv.id, "title": conv.title}


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deletes a conversation thread and cascades deletion of its message history.
    """
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation thread not found.")

    db.delete(conv)
    db.commit()

    return {"detail": "Conversation deleted successfully", "id": conversation_id}


# ---------------------------------------------------------------------------
# Legacy Query & Suggestion Endpoints (Kept 100% Backwards-Compatible)
# ---------------------------------------------------------------------------

@router.post("/query", response_model=AssistantQueryResponse)
def query_financial_assistant(
    request: AssistantQueryRequest,
    http_request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits a natural language query to the intelligent financial assistant.
    The response is grounded exclusively in the active business's ledger
    records, subscription commitments, and forecast models.

    Tenant Isolation: Queries are strictly filtered by current_user.id and active business.
    """
    biz = get_active_business(current_user=current_user, db=db, request=http_request)

    subscriptions = get_environment_subscriptions(db=db, biz=biz, request=http_request)
    transactions = get_environment_transactions(db=db, biz=biz, request=http_request)

    return FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=subscriptions,
        transactions=transactions,
        request=request,
        db=db,
    )


@router.get("/suggestions", response_model=AssistantSuggestionsResponse)
def get_assistant_suggestions(
    http_request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns starter conversation prompts dynamically tailored to whether the business
    has sufficient or insufficient operating data.
    """
    biz = get_active_business(current_user=current_user, db=db, request=http_request)

    subscriptions = get_environment_subscriptions(db=db, biz=biz, request=http_request)
    transactions = get_environment_transactions(db=db, biz=biz, request=http_request)

    return FinancialAssistantEngine.get_starter_suggestions(
        business=biz,
        subscriptions=subscriptions,
        transactions=transactions,
    )


@router.get("/provider-status")
def get_assistant_provider_status(
    http_request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the operational status of the AI Assistant backend without revealing credentials.
    """
    biz = get_active_business(current_user=current_user, db=db, request=http_request)
    is_llm = FinancialAssistantEngine.is_llm_configured()
    return {
        "status": "active",
        "llm_provider_configured": is_llm,
        "active_generation_model": (
            "Google Gemini 1.5 Flash (Hybrid Augmentation)"
            if is_llm
            else "SubWise Deterministic Intelligence Engine"
        ),
        "deterministic_engine": "SubWise Deterministic Intelligence Engine",
        "fallback_available": True,
        "secrets_exposed": False,
        "company_name": biz.company_name
    }
