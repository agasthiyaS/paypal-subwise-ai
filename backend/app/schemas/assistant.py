from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AssistantQueryRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    conversation_id: Optional[str] = None
    context_hint: Optional[str] = None  # e.g. "dashboard", "reports", "forecast", "subscriptions"


class EvidenceCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    data_type: str  # 'actual', 'projected', 'contractual', 'simulation', 'informational'
    amount: Optional[float] = None
    currency: str = "USD"
    details: Dict[str, Any] = {}
    navigation_link: Optional[str] = None
    badge_label: Optional[str] = None
    badge_status: Optional[str] = "neutral"  # 'success', 'warning', 'danger', 'neutral', 'info'


class ChatAction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    path: str
    description: Optional[str] = None


class AssistantQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    response_text: str
    is_ai_generated: bool
    generation_model: str
    intent: str
    data_sufficiency_status: str  # 'sufficient_data', 'limited_data', 'insufficient_data'
    evidence_cards: List[EvidenceCard] = []
    suggested_followups: List[str] = []
    actions: List[ChatAction] = []
    reporting_period: Optional[str] = None
    disclaimer: str
    llm_provider_configured: bool = False


class SuggestionItem(BaseModel):
    prompt: str
    category: str  # 'subscriptions', 'forecast', 'affordability', 'health', 'reports'
    label: str


class AssistantSuggestionsResponse(BaseModel):
    suggestions: List[SuggestionItem] = []
    data_sufficiency_status: str
    llm_provider_configured: bool = False
    active_engine: str = "SubWise Deterministic Engine"


# ---------------------------------------------------------------------------
# Conversational Chatbot Schemas (Phase 9)
# ---------------------------------------------------------------------------

class ChatMessageItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    conversation_id: str
    role: str  # 'user' | 'assistant'
    content: str
    meta_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class ChatConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    account_type: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: Optional[str] = None


class ChatConversationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    account_type: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageItem] = []


class ChatMessageRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None
    context_hint: Optional[str] = None


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: str
    title: Optional[str] = None
    message: str
    provider: str = "deterministic"  # 'gemini' | 'deterministic'
    is_ai_generated: bool = False
    generation_model: str
    intent: str
    data_sufficiency_status: str
    evidence_cards: List[EvidenceCard] = []
    suggested_followups: List[str] = []
    actions: List[ChatAction] = []
    disclaimer: Optional[str] = None
    reporting_period: Optional[str] = None
    created_at: Optional[str] = None


class ConversationRenameRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, max_length=255)


