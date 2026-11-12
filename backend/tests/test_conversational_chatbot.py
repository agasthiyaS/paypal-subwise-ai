"""
Phase 9: Conversational AI Chatbot Test Suite
Tests for:
1. Read-only safety guard action interceptor
2. Multi-account intelligence (Individual, Household, Business)
3. Conversational chat persistence and message threads in DB
4. Tenant and user isolation
5. Contextual follow-up memory
6. Deterministic fallback when Gemini is unavailable
"""
import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.expense import Expense
from app.models.household_member import HouseholdMember
from app.models.budget import Budget
from app.models.conversation import Conversation, ChatMessage
from app.schemas.assistant import AssistantQueryRequest, ChatMessageRequest, ConversationRenameRequest
from app.services.financial_assistant_engine import FinancialAssistantEngine
from app.api.assistant import (
    chat_financial_assistant,
    list_conversations,
    get_conversation_detail,
    rename_conversation,
    delete_conversation,
)
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Test SQLite In-Memory Database Fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


def _create_user_and_biz(db, user_id=1, email="test@subwise.ai", account_type="business", cash=20000.0):
    user = User(id=user_id, email=email, hashed_password="hashed_pw", is_active=True)
    db.add(user)
    db.flush()

    biz = BusinessProfile(
        id=user_id * 10,
        user_id=user.id,
        company_name=f"SubWise {account_type.capitalize()}",
        account_type=account_type,
        current_cash_reserves=cash,
        currency="USD",
    )
    db.add(biz)
    db.commit()
    return user, biz


# ---------------------------------------------------------------------------
# 1. READ-ONLY SAFETY GUARD TESTS
# ---------------------------------------------------------------------------
def test_read_only_action_guard():
    """Verify that mutation requests are strictly intercepted with guidance."""
    user = User(id=1, email="u1@test.com")
    biz = BusinessProfile(id=10, user_id=1, company_name="Test Co", account_type="business")

    # Mutation triggers
    test_prompts = [
        "cancel my subscription to Netflix",
        "cancel Netflix",
        "pay my bill now",
        "send money to vendor",
        "transfer money",
        "delete transaction",
        "change budget to $500",
    ]

    for p in test_prompts:
        req = AssistantQueryRequest(message=p)
        res = FinancialAssistantEngine.process_query(
            business=biz,
            subscriptions=[],
            transactions=[],
            request=req,
        )
        assert res.intent == "READ_ONLY_GUARD", f"Failed to intercept: {p}"
        assert "Read-Only" in res.response_text
        assert len(res.actions) > 0
        action_paths = [a.path for a in res.actions]
        assert "/subscriptions" in action_paths


# ---------------------------------------------------------------------------
# 2. MULTI-ACCOUNT STARTER SUGGESTIONS
# ---------------------------------------------------------------------------
def test_multi_account_starter_suggestions():
    """Verify that starter prompts adapt to Individual, Household, and Business."""
    # Individual
    biz_ind = BusinessProfile(id=1, user_id=1, company_name="Personal", account_type="individual")
    res_ind = FinancialAssistantEngine.get_starter_suggestions(business=biz_ind, subscriptions=[], transactions=[])
    prompts_ind = " ".join(s.prompt for s in res_ind.suggestions).lower()
    assert "money go" in prompts_ind or "subscriptions" in prompts_ind

    # Household
    biz_hh = BusinessProfile(id=2, user_id=2, company_name="Family Pool", account_type="household")
    res_hh = FinancialAssistantEngine.get_starter_suggestions(business=biz_hh, subscriptions=[], transactions=[])
    prompts_hh = " ".join(s.prompt for s in res_hh.suggestions).lower()
    assert "household" in prompts_hh or "member" in prompts_hh

    # Business
    biz_b = BusinessProfile(id=3, user_id=3, company_name="Apex Corp", account_type="business")
    res_b = FinancialAssistantEngine.get_starter_suggestions(business=biz_b, subscriptions=[], transactions=[])
    prompts_b = " ".join(s.prompt for s in res_b.suggestions).lower()
    assert "status" in prompts_b or "cash" in prompts_b or "runway" in prompts_b


# ---------------------------------------------------------------------------
# 3. INDIVIDUAL SPENDING BREAKDOWN
# ---------------------------------------------------------------------------
def test_individual_spending_breakdown(db_session):
    """Verify that Individual account computes categorized expenses from Expense table."""
    user, biz = _create_user_and_biz(db_session, user_id=1, account_type="individual")

    # Add individual expenses
    now = datetime.datetime.utcnow()
    e1 = Expense(business_id=biz.id, user_id=user.id, amount=120.0, expense_type="expense", category="Food & Groceries", description="Trader Joe's", expense_date=now)
    e2 = Expense(business_id=biz.id, user_id=user.id, amount=80.0, expense_type="expense", category="Entertainment", description="Cinema & Games", expense_date=now)
    e3 = Expense(business_id=biz.id, user_id=user.id, amount=50.0, expense_type="expense", category="Food & Groceries", description="Local Market", expense_date=now)
    db_session.add_all([e1, e2, e3])
    db_session.commit()

    req = AssistantQueryRequest(message="Where did most of my money go this month?")
    res = FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=[],
        transactions=[],
        request=req,
        db=db_session,
    )

    assert res.intent == "SPENDING_BREAKDOWN"
    assert "Food & Groceries" in res.response_text
    assert "$170.00" in res.response_text or "$250.00" in res.response_text
    assert len(res.actions) > 0


# ---------------------------------------------------------------------------
# 4. HOUSEHOLD MEMBER SPENDING
# ---------------------------------------------------------------------------
def test_household_member_spending(db_session):
    """Verify that Household account computes member-wise attribution."""
    user, biz = _create_user_and_biz(db_session, user_id=2, account_type="household")

    # Add members
    m1 = HouseholdMember(business_id=biz.id, name="Alex", role="Primary", is_active=True)
    m2 = HouseholdMember(business_id=biz.id, name="Taylor", role="Partner", is_active=True)
    db_session.add_all([m1, m2])
    db_session.flush()

    # Add expenses attributed to members
    now = datetime.datetime.utcnow()
    exp1 = Expense(business_id=biz.id, user_id=user.id, household_member_id=m1.id, amount=300.0, expense_type="expense", category="Rent & Housing", description="Apartment share", expense_date=now)
    exp2 = Expense(business_id=biz.id, user_id=user.id, household_member_id=m2.id, amount=150.0, expense_type="expense", category="Groceries", description="Whole Foods", expense_date=now)
    db_session.add_all([exp1, exp2])
    db_session.commit()

    req = AssistantQueryRequest(message="Who spent the most in our household this month?")
    res = FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=[],
        transactions=[],
        request=req,
        db=db_session,
    )

    assert res.intent == "HOUSEHOLD_SPENDING"
    assert "Alex" in res.response_text
    assert "Taylor" in res.response_text
    assert "$300.00" in res.response_text
    assert any(a.path == "/household" for a in res.actions)


# ---------------------------------------------------------------------------
# 5. CONTEXTUAL FOLLOW-UP
# ---------------------------------------------------------------------------
def test_contextual_followup():
    """Verify contextual follow-ups handle multi-turn inquiries."""
    biz = BusinessProfile(id=1, user_id=1, company_name="Acme Corp", account_type="business")
    req = AssistantQueryRequest(message="What about last month?")
    history = [
        {"role": "user", "content": "Where did most of my money go?"},
        {"role": "assistant", "content": "Total outflows were $4,200."},
    ]
    res = FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=[],
        transactions=[],
        request=req,
        history=history,
    )
    assert res.intent == "CONTEXTUAL_FOLLOWUP"
    assert "Historical Comparison" in res.response_text or "prior billing cycle" in res.response_text


# ---------------------------------------------------------------------------
# 6. CONVERSATION PERSISTENCE, THREADS & TENANT ISOLATION
# ---------------------------------------------------------------------------
def test_conversational_chat_persistence_and_isolation(db_session):
    """Verify conversational chatbot creates threads, preserves history, and isolates users."""
    user1, biz1 = _create_user_and_biz(db_session, user_id=10, email="u10@test.com", account_type="business")
    user2, biz2 = _create_user_and_biz(db_session, user_id=20, email="u20@test.com", account_type="individual")

    # 1. User 1 sends first message (no conversation_id -> auto-creates thread)
    req1 = ChatMessageRequest(message="What subscriptions am I currently paying for?")
    chat_res1 = chat_financial_assistant(request=req1, current_user=user1, db=db_session)

    conv_id = chat_res1.conversation_id
    assert conv_id.startswith("conv_")
    assert chat_res1.title is not None
    assert chat_res1.message is not None

    # Verify records in database
    db_conv = db_session.query(Conversation).filter(Conversation.id == conv_id).first()
    assert db_conv is not None
    assert db_conv.user_id == user1.id
    assert len(db_conv.messages) == 2  # 1 user + 1 assistant

    # 2. User 1 sends follow-up in same conversation
    req2 = ChatMessageRequest(message="What are my upcoming renewals?", conversation_id=conv_id)
    chat_res2 = chat_financial_assistant(request=req2, current_user=user1, db=db_session)
    assert chat_res2.conversation_id == conv_id

    # Verify conversation now has 4 messages
    db_session.refresh(db_conv)
    assert len(db_conv.messages) == 4

    # 3. List conversations for User 1
    u1_convs = list_conversations(current_user=user1, db=db_session)
    assert len(u1_convs) == 1
    assert u1_convs[0].id == conv_id
    assert u1_convs[0].message_count == 4

    # 4. User Isolation: User 2 sees 0 conversations
    u2_convs = list_conversations(current_user=user2, db=db_session)
    assert len(u2_convs) == 0

    # User 2 cannot access User 1's conversation
    with pytest.raises(HTTPException) as exc:
        get_conversation_detail(conversation_id=conv_id, current_user=user2, db=db_session)
    assert exc.value.status_code == 404

    # User 2 cannot delete User 1's conversation
    with pytest.raises(HTTPException) as exc:
        delete_conversation(conversation_id=conv_id, current_user=user2, db=db_session)
    assert exc.value.status_code == 404

    # 5. Rename Conversation for User 1
    rename_req = ConversationRenameRequest(title="Software Renewals Q4")
    ren_res = rename_conversation(conversation_id=conv_id, payload=rename_req, current_user=user1, db=db_session)
    assert ren_res["title"] == "Software Renewals Q4"

    # 6. Delete Conversation for User 1
    del_res = delete_conversation(conversation_id=conv_id, current_user=user1, db=db_session)
    assert del_res["detail"] == "Conversation deleted successfully"

    # Ensure conversation and messages are cascade deleted
    assert db_session.query(Conversation).filter(Conversation.id == conv_id).first() is None
    assert db_session.query(ChatMessage).filter(ChatMessage.conversation_id == conv_id).count() == 0


# ---------------------------------------------------------------------------
# 7. NATURAL CONVERSATIONAL & GENERAL KNOWLEDGE TESTS (Phase 10 Upgrade)
# ---------------------------------------------------------------------------
def test_natural_greetings():
    """Verify natural human-like greeting responses without premature financial table dumps."""
    biz = BusinessProfile(id=1, user_id=1, company_name="Test User", account_type="individual")

    for greeting in ["Hii!", "Hello", "Hey", "Good morning", "Hey there"]:
        res = FinancialAssistantEngine.process_query(
            business=biz,
            subscriptions=[],
            transactions=[],
            request=AssistantQueryRequest(message=greeting),
            history=[],
        )
        assert res.intent == "CASUAL_CONVERSATION", f"Failed for {greeting}"
        assert not res.is_ai_generated  # Deterministic when no Gemini
        assert "SubWise AI assistant" in res.response_text or "How's it going" in res.response_text or "What can I help" in res.response_text
        assert len(res.evidence_cards) == 0  # No intrusive cards on greetings


def test_subsequent_greeting_avoids_reintroduction():
    """Verify assistant does not repeatedly introduce itself when history already exists."""
    biz = BusinessProfile(id=1, user_id=1, company_name="Test User", account_type="individual")

    history = [
        {"role": "user", "content": "Hii!"},
        {"role": "assistant", "content": "Hey! How's it going? I'm your SubWise AI assistant. What can I help you with today?"},
    ]

    res = FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=[],
        transactions=[],
        request=AssistantQueryRequest(message="Hey again"),
        history=history,
    )
    assert res.intent == "CASUAL_CONVERSATION"
    assert "Hey again" in res.response_text or "Hello" in res.response_text
    assert "I'm your SubWise AI assistant" not in res.response_text  # Avoids repetitive self-introduction


def test_casual_checkins():
    """Verify natural conversational responses to 'How are you?', 'What are you doing?', and 'What's up?'."""
    biz = BusinessProfile(id=1, user_id=1, company_name="Test User", account_type="business")

    # How are you?
    r_how = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message="How are you?"))
    assert r_how.intent == "CASUAL_CONVERSATION"
    assert "doing well" in r_how.response_text.lower() or "great" in r_how.response_text.lower()
    assert len(r_how.evidence_cards) == 0

    # What are you doing?
    r_doing = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message="What are you doing?"))
    assert r_doing.intent == "CASUAL_CONVERSATION"
    assert "here and ready to help" in r_doing.response_text.lower() or "keeping track" in r_doing.response_text.lower()

    # What's up?
    r_up = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message="What's up?"))
    assert r_up.intent == "CASUAL_CONVERSATION"
    assert "ready to help" in r_up.response_text.lower() or "not much" in r_up.response_text.lower()


def test_appreciation_and_farewells():
    """Verify friendly appreciation acknowledgments and farewell responses."""
    biz = BusinessProfile(id=1, user_id=1, company_name="Test User", account_type="individual")

    # Thank you
    for thx in ["Thank you", "Thanks", "Awesome, thanks a lot", "Thank you so much"]:
        r_thx = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message=thx))
        assert r_thx.intent == "CASUAL_CONVERSATION", f"Failed on: {thx}"
        assert "welcome" in r_thx.response_text.lower() or "glad" in r_thx.response_text.lower()
        assert len(r_thx.evidence_cards) == 0

    # Farewells
    for bye in ["Bye", "Goodbye", "See you later", "Good night"]:
        r_bye = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message=bye))
        assert r_bye.intent == "CASUAL_CONVERSATION", f"Failed on: {bye}"
        assert any(k in r_bye.response_text.lower() for k in ["goodbye", "good night", "take care", "see you", "great day"])


def test_boredom_and_casual_engagement():
    """Verify engaging responses to 'I'm bored' and 'Tell me something interesting'."""
    biz = BusinessProfile(id=1, user_id=1, company_name="Test User", account_type="individual")

    # I'm bored
    r_bored = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message="I'm bored."))
    assert r_bored.intent == "CASUAL_CONVERSATION"
    assert "interesting" in r_bored.response_text.lower() or "learn" in r_bored.response_text.lower() or "chat" in r_bored.response_text.lower()

    # Tell me something interesting
    r_fact = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message="Tell me something interesting"))
    assert r_fact.intent == "CASUAL_CONVERSATION"
    assert "salary" in r_fact.response_text.lower() or "interesting" in r_fact.response_text.lower() or "fact" in r_fact.response_text.lower()


def test_general_knowledge_questions():
    """Verify educational concept explanations without inventing fake user accounts."""
    biz = BusinessProfile(id=1, user_id=1, company_name="Test User", account_type="business")

    # 1. Machine Learning
    r_ml = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message="Explain machine learning"))
    assert r_ml.intent == "GENERAL_KNOWLEDGE"
    assert "machine learning" in r_ml.response_text.lower()
    assert "learn patterns" in r_ml.response_text.lower() or "predictions" in r_ml.response_text.lower()
    assert len(r_ml.evidence_cards) == 0

    # 2. Inflation
    r_inf = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message="What is inflation?"))
    assert r_inf.intent == "GENERAL_KNOWLEDGE"
    assert "purchasing power" in r_inf.response_text.lower() or "prices" in r_inf.response_text.lower()

    # 3. Compound Interest
    r_ci = FinancialAssistantEngine.process_query(biz, [], [], AssistantQueryRequest(message="What is compound interest?"))
    assert r_ci.intent == "GENERAL_KNOWLEDGE"
    assert "interest" in r_ci.response_text.lower()
    assert "principal" in r_ci.response_text.lower() or "interest on" in r_ci.response_text.lower()


def test_conversation_mode_transitions():
    """
    Verify bidirectional transition between casual conversation and financial intelligence:
    1. Casual greeting
    2. General knowledge explanation
    3. Financial data inquiry (grounded in actual records)
    4. Financial follow-up
    5. Casual appreciation & farewell
    """
    biz = BusinessProfile(id=1, user_id=1, company_name="Transition Corp", account_type="business", monthly_baseline_revenue=6000.0)
    sub = Subscription(id=1, business_id=1, vendor_name="CloudSaaS", latest_amount=35.0, average_amount=35.0, cadence="monthly", status="active")

    conv = []

    # Turn 1: Casual Greeting
    req1 = AssistantQueryRequest(message="Hii!")
    res1 = FinancialAssistantEngine.process_query(biz, [sub], [], req1, history=conv)
    assert res1.intent == "CASUAL_CONVERSATION"
    assert len(res1.evidence_cards) == 0
    conv.append({"role": "user", "content": "Hii!"})
    conv.append({"role": "assistant", "content": res1.response_text})

    # Turn 2: General Knowledge
    req2 = AssistantQueryRequest(message="Explain machine learning.")
    res2 = FinancialAssistantEngine.process_query(biz, [sub], [], req2, history=conv)
    assert res2.intent == "GENERAL_KNOWLEDGE"
    conv.append({"role": "user", "content": "Explain machine learning."})
    conv.append({"role": "assistant", "content": res2.response_text})

    # Turn 3: Transition to Financial Question (Actual database records)
    req3 = AssistantQueryRequest(message="What subscriptions am I currently paying for?")
    res3 = FinancialAssistantEngine.process_query(biz, [sub], [], req3, history=conv)
    assert res3.intent == "SPEND_OVERVIEW"
    assert "CloudSaaS" in res3.response_text
    assert "$35.00" in res3.response_text
    conv.append({"role": "user", "content": "What subscriptions am I currently paying for?"})
    conv.append({"role": "assistant", "content": res3.response_text})

    # Turn 4: Financial Contextual Follow-up
    req4 = AssistantQueryRequest(message="What about last month?")
    res4 = FinancialAssistantEngine.process_query(biz, [sub], [], req4, history=conv)
    assert res4.intent == "CONTEXTUAL_FOLLOWUP"
    assert "Historical Comparison" in res4.response_text or "prior billing cycle" in res4.response_text
    conv.append({"role": "user", "content": "What about last month?"})
    conv.append({"role": "assistant", "content": res4.response_text})

    # Turn 5: Transition back to Casual Appreciation
    req5 = AssistantQueryRequest(message="Thank you!")
    res5 = FinancialAssistantEngine.process_query(biz, [sub], [], req5, history=conv)
    assert res5.intent == "CASUAL_CONVERSATION"
    assert "welcome" in res5.response_text.lower()
    conv.append({"role": "user", "content": "Thank you!"})
    conv.append({"role": "assistant", "content": res5.response_text})

    # Turn 6: Farewell
    req6 = AssistantQueryRequest(message="Bye!")
    res6 = FinancialAssistantEngine.process_query(biz, [sub], [], req6, history=conv)
    assert res6.intent == "CASUAL_CONVERSATION"
    assert "goodbye" in res6.response_text.lower() or "great day" in res6.response_text.lower()
