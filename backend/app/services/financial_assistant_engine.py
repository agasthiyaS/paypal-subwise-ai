"""
Stage 7: Intelligent Financial Assistant Engine
Provides authenticated, evidence-grounded financial Q&A for SMBs.

Core Principles:
1. Zero Hallucination: Every financial figure is calculated deterministically from
   verified ledger records, payment schedules, or simulation formulas.
2. AI-Enhanced with Transparent Fallback: If external LLM (Gemini 1.5 Flash) is available,
   it interprets questions and explains structured facts under strict guardrails.
   If unavailable or rate-limited, the deterministic engine answers every supported intent.
3. Affordability & Simulation Integration: Questions like "Can I afford X?" route to
   RecommendationEngine.simulate_purchase rather than using LLM math.
4. Report Integration: Queries requesting report summaries route to ReportEngine.
5. Structured Evidence Cards: Responses include verifiable metrics, data types,
   provenance disclosures, and deep navigation links for the frontend.
"""
import re
import datetime
from typing import List, Dict, Any, Optional, Tuple
import httpx

from app.config import settings
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    EvidenceCard,
    SuggestionItem,
    AssistantSuggestionsResponse,
    ChatAction,
)
from app.schemas.recommendation import PurchaseSimulationRequest
from app.services.forecast_engine import ForecastEngine
from app.services.subscription_analyzer import SubscriptionExpenseAnalyzer
from app.services.recommendation_engine import RecommendationEngine
from app.services.financial_intelligence_engine import FinancialIntelligenceEngine
from app.services.report_engine import ReportEngine
from app.services.vendor_comparison_service import VendorComparisonService
from app.services.smart_spending_service import SmartSpendingService


class FinancialAssistantEngine:

    @classmethod
    def is_llm_configured(cls) -> bool:
        """
        Safely detects whether a valid Gemini API key is configured.
        Never reveals the secret key in returns, logs, or error messages.
        Requires non-empty string, length >= 16, and not placeholder values.
        """
        raw_key = (settings.GEMINI_API_KEY or settings.LLM_API_KEY or "").strip()
        if not raw_key:
            return False
        if len(raw_key) < 16 or raw_key.lower().startswith(("your_", "my_", "test_", "placeholder", "subwise_")):
            return False
        return True

    @classmethod
    def get_starter_suggestions(
        cls,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
    ) -> AssistantSuggestionsResponse:
        """
        Returns dynamic conversation starters tailored to the business's data sufficiency status.
        """
        confirmed_subs = [s for s in subscriptions if (s.status or "").lower() == "active"]
        valid_txs = [t for t in transactions if ForecastEngine.is_valid_operating(t)]
        is_llm = cls.is_llm_configured()

        account_type = (business.account_type or "business").lower()

        if not valid_txs and not confirmed_subs:
            status = "insufficient_data"
            if account_type == "individual":
                suggestions = [
                    SuggestionItem(
                        prompt="Where did most of my money go this month?",
                        category="health",
                        label="Spending Breakdown"
                    ),
                    SuggestionItem(
                        prompt="What subscriptions am I currently paying for?",
                        category="subscriptions",
                        label="Active Subscriptions"
                    ),
                    SuggestionItem(
                        prompt="Can I afford a new subscription for $30/month?",
                        category="affordability",
                        label="Simulate $30/mo"
                    ),
                    SuggestionItem(
                        prompt="Find cheaper alternatives for my streaming and software",
                        category="reports",
                        label="Find Cheaper Plans"
                    ),
                ]
            elif account_type == "household":
                suggestions = [
                    SuggestionItem(
                        prompt="How much did each household member spend this month?",
                        category="health",
                        label="Member Spending"
                    ),
                    SuggestionItem(
                        prompt="Are we on track with our household monthly budget?",
                        category="forecast",
                        label="Household Budget"
                    ),
                    SuggestionItem(
                        prompt="What shared recurring subscriptions are active?",
                        category="subscriptions",
                        label="Shared Subscriptions"
                    ),
                    SuggestionItem(
                        prompt="Where can our household cut costs to save $150/month?",
                        category="reports",
                        label="Household Savings"
                    ),
                ]
            else:
                suggestions = [
                    SuggestionItem(
                        prompt="What is my current financial status and what data is missing?",
                        category="health",
                        label="Data Status & Gaps"
                    ),
                    SuggestionItem(
                        prompt="Can I afford a new project management tool for $40/month?",
                        category="affordability",
                        label="Simulate $40/mo Tool"
                    ),
                    SuggestionItem(
                        prompt="How does PayPal SubWise track subscriptions and cash flow?",
                        category="reports",
                        label="Methodology Overview"
                    ),
                    SuggestionItem(
                        prompt="What starting cash balance is configured for my business?",
                        category="forecast",
                        label="Check Starting Cash"
                    ),
                ]
        else:
            status = "sufficient_data" if len(valid_txs) >= 10 else "limited_data"
            if account_type == "individual":
                suggestions = [
                    SuggestionItem(
                        prompt="Where did most of my money go this month?",
                        category="health",
                        label="Spending Breakdown"
                    ),
                    SuggestionItem(
                        prompt="What are my upcoming subscription renewals over the next 30 days?",
                        category="subscriptions",
                        label="Upcoming Renewals"
                    ),
                    SuggestionItem(
                        prompt="Can I afford a new subscription for $45/month?",
                        category="affordability",
                        label="Simulate $45/mo"
                    ),
                    SuggestionItem(
                        prompt="Find cheaper alternatives for my recurring software",
                        category="reports",
                        label="Find Cheaper Plans"
                    ),
                    SuggestionItem(
                        prompt="What is my financial health score and how can I improve it?",
                        category="health",
                        label="Health Score"
                    ),
                ]
            elif account_type == "household":
                suggestions = [
                    SuggestionItem(
                        prompt="How much did each household member spend this month?",
                        category="health",
                        label="Member Spending"
                    ),
                    SuggestionItem(
                        prompt="Are we exceeding our household monthly budget?",
                        category="forecast",
                        label="Budget Pacing"
                    ),
                    SuggestionItem(
                        prompt="What are our upcoming shared subscription renewals?",
                        category="subscriptions",
                        label="Shared Renewals"
                    ),
                    SuggestionItem(
                        prompt="Where can our household cut costs to save $150/month?",
                        category="reports",
                        label="Household Savings"
                    ),
                    SuggestionItem(
                        prompt="What is our household financial health score?",
                        category="health",
                        label="Household Health"
                    ),
                ]
            else:
                suggestions = [
                    SuggestionItem(
                        prompt="What are my upcoming subscription renewals over the next 30 days?",
                        category="subscriptions",
                        label="Upcoming Renewals"
                    ),
                    SuggestionItem(
                        prompt="What is our projected cash runway and monthly burn rate?",
                        category="forecast",
                        label="Cash Runway & Burn"
                    ),
                    SuggestionItem(
                        prompt="Can we afford to upgrade to an enterprise software plan for $150/month?",
                        category="affordability",
                        label="Simulate $150/mo Purchase"
                    ),
                    SuggestionItem(
                        prompt="Summarize our latest monthly financial report and operating cash flow.",
                        category="reports",
                        label="Monthly Financial Summary"
                    ),
                    SuggestionItem(
                        prompt="What is our financial health score and what risks should we watch?",
                        category="health",
                        label="Health Score & Risks"
                    ),
                ]

        return AssistantSuggestionsResponse(
            suggestions=suggestions,
            data_sufficiency_status=status,
            llm_provider_configured=is_llm,
            active_engine="Google Gemini 1.5 Flash (Hybrid Augmentation)" if is_llm else "SubWise Deterministic Engine"
        )

    # -------------------------------------------------------------------------
    # Conversational Intelligence & Intent Classification (Phase 10 Upgrade)
    # -------------------------------------------------------------------------
    @classmethod
    def _get_casual_subtype(cls, message: str) -> str:
        m = message.lower().strip()
        clean = re.sub(r"[^\w\s]", "", m).strip()

        # Greetings
        if re.search(r"^(hi+|hello+|hey+|howdy|good\s+(morning|afternoon|evening|day)|greetings|yo|sup)\b", clean):
            return "greeting"

        # Checkin / Status
        if any(p in clean for p in [
            "how are you", "how are u", "how r u", "hows it going", "how is it going",
            "how have you been", "what are you doing", "what r u doing", "what are u doing",
            "what are you up to", "what is up", "whats up", "what's up", "who are you",
            "what can you do", "introduce yourself", "tell me about yourself", "what is your name"
        ]):
            return "checkin"

        # Appreciation
        if any(p in clean for p in [
            "thanks", "thank you", "thank u", "thx", "appreciate it", "great", "awesome",
            "perfect", "cool", "nice", "good job", "well done", "sounds good", "that helps", "got it"
        ]) and len(clean.split()) <= 6:
            return "appreciation"

        # Farewells
        if any(p in clean for p in [
            "bye", "goodbye", "see you", "see ya", "see you later", "good night", "goodnight",
            "catch you later", "take care", "have a good one", "talk to you later"
        ]) and len(clean.split()) <= 6:
            return "farewell"

        # Boredom & Entertainment
        if any(p in clean for p in [
            "bored", "im bored", "i am bored", "tell me something interesting", "tell me a joke",
            "make me laugh", "tell me a fun fact", "random fact", "entertain me",
            "what should we talk about", "talk to me", "can we chat", "lets chat"
        ]):
            return "boredom"

        return "general_casual"

    @classmethod
    def _get_knowledge_subtype(cls, message: str) -> str:
        m = message.lower().strip()
        if "machine learning" in m or re.search(r"\bml\b", m):
            return "machine_learning"
        if "artificial intelligence" in m or re.search(r"\bai\b", m):
            return "ai"
        if "deep learning" in m:
            return "deep_learning"
        if "inflation" in m:
            return "inflation"
        if "compound interest" in m:
            return "compound_interest"
        if "credit score" in m:
            return "credit_score"
        if "cash flow" in m:
            return "cash_flow"
        if "blockchain" in m or "crypto" in m:
            return "blockchain"
        if "cloud computing" in m:
            return "cloud_computing"
        if "quantum computing" in m:
            return "quantum_computing"
        if "opportunity cost" in m:
            return "opportunity_cost"
        if "emergency fund" in m:
            return "emergency_fund"
        if re.search(r"\bpython\b", m):
            return "python"
        return "general_concept"

    @classmethod
    def classify_conversational_type(
        cls,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Classifies incoming user messages into conversational, educational, or fintech intent categories.
        Ensures everyday chat is not forced into financial ledger inquiries.
        """
        m = message.lower().strip()
        clean = re.sub(r"[^\w\s]", "", m).strip()

        # 0. Read-Only Safety Guard: Mutating requests (Strict Security Boundary)
        if any(p in m for p in [
            "cancel subscription", "cancel my subscription", "cancel netflix", "cancel spotify",
            "cancel hulu", "unsubscribe", "cancel service", "stop subscription", "cancel payment",
            "pay bill", "pay my bill", "pay this invoice", "make payment", "send money", "transfer money",
            "execute payment", "process payment", "change budget", "update budget", "set budget",
            "increase budget", "lower budget", "delete expense", "delete transaction", "remove subscription",
            "add expense", "create subscription", "transfer funds"
        ]) or (m.startswith(("cancel ", "pay ", "delete ", "transfer ", "send money", "modify budget")) and len(m.split()) <= 6):
            return "READ_ONLY_GUARD", None

        # Check for presence of explicit personal financial indicators
        personal_finance_tokens = [
            "my spending", "my budget", "my revenue", "my subscription", "my subscriptions",
            "my money", "my account", "my expense", "my expenses", "my cash", "our spending",
            "our budget", "our revenue", "our subscription", "our subscriptions", "our money",
            "our account", "our expense", "our expenses", "our runway", "did i spend",
            "how much did i spend", "what did i spend", "can i afford", "can we afford",
            "am i over budget", "are we over budget", "who spent", "household member",
            "household members", "shared expenses", "member breakdown", "who is spending"
        ]
        has_personal_finance = any(tok in m for tok in personal_finance_tokens)

        # 1. Casual Conversation: Greetings, Check-ins, Appreciation, Farewells, Boredom
        if not has_personal_finance:
            # Greetings
            if re.search(r"^(hi+|hello+|hey+|howdy|good\s+(morning|afternoon|evening|day)|greetings|yo|sup)\b", clean) and len(clean.split()) <= 4:
                return "CASUAL_CONVERSATION", cls._get_casual_subtype(message)

            # Checkin
            if any(p in clean for p in [
                "how are you", "how are u", "how r u", "hows it going", "how is it going",
                "how have you been", "what are you doing", "what r u doing", "what are u doing",
                "what are you up to", "what is up", "whats up", "what's up", "who are you",
                "what can you do", "introduce yourself", "tell me about yourself"
            ]):
                return "CASUAL_CONVERSATION", "checkin"

            # Appreciation
            if any(p in clean for p in [
                "thanks", "thank you", "thank u", "thx", "appreciate it", "great", "awesome",
                "perfect", "cool", "nice", "good job", "well done", "sounds good", "that helps", "got it"
            ]) and len(clean.split()) <= 5:
                return "CASUAL_CONVERSATION", "appreciation"

            # Farewells
            if any(p in clean for p in [
                "bye", "goodbye", "see you", "see ya", "see you later", "good night", "goodnight",
                "catch you later", "take care", "have a good one", "talk to you later"
            ]) and len(clean.split()) <= 5:
                return "CASUAL_CONVERSATION", "farewell"

            # Boredom & Entertainment
            if any(p in clean for p in [
                "bored", "im bored", "i am bored", "tell me something interesting", "tell me a joke",
                "make me laugh", "tell me a fun fact", "random fact", "entertain me",
                "what should we talk about", "talk to me", "can we chat", "lets chat"
            ]):
                return "CASUAL_CONVERSATION", "boredom"

        # 2. Contextual Follow-up (Phase 9 Contextual Memory across turns)
        if any(p in m for p in [
            "what about last month", "and last month", "previous month", "how about last month",
            "why did it increase", "why is it high", "why is that", "explain why",
            "show more details", "tell me more", "break that down", "how does that work",
            "how does it", "how do they", "how so", "can you elaborate", "elaborate on that"
        ]):
            # Check if previous context was general knowledge or financial
            prev_was_knowledge = False
            if history and len(history) >= 2:
                for h in reversed(history[:-1]):
                    u_text = h.get("content", "").lower()
                    if any(k in u_text for k in ["machine learning", "artificial intelligence", "inflation", "blockchain", "quantum", "compound interest"]):
                        prev_was_knowledge = True
                        break
            if prev_was_knowledge:
                return "CONTEXTUAL_FOLLOWUP", "knowledge"
            return "CONTEXTUAL_FOLLOWUP", "financial"

        # 3. General Knowledge / Educational Questions
        # e.g., "explain machine learning", "what is inflation", "how does compound interest work"
        if not has_personal_finance and (
            m.startswith(("explain ", "what is ", "what are ", "how does ", "how do ", "define ", "tell me about ", "why is ", "who is ", "who was "))
            or "difference between" in m
        ):
            account_words = ["my", "our", "i", "we", "me", "us", "mine", "account", "business", "company", "budget", "spending", "subscription", "runway", "balance", "paypal"]
            if not any(re.search(rf"\b{w}\b", m) for w in account_words):
                return "GENERAL_KNOWLEDGE", cls._get_knowledge_subtype(message)

        # 4. Household Member Spending
        if any(p in m for p in [
            "who spent the most", "who spent more", "member spending", "partner spending",
            "household member", "household members", "shared expenses", "member breakdown",
            "who is spending", "roommate spending", "how much did each member spend"
        ]):
            return "HOUSEHOLD_SPENDING", None

        # 5. Vendor Alternatives & Cheaper Plans
        if any(p in m for p in [
            "cheaper alternative", "alternative to", "switch provider", "cheaper plan",
            "cheaper tier", "compare vendor", "find alternatives", "cheaper options",
            "alternatives for", "cheaper software", "cheaper streaming", "substitute",
            "cheaper alternatives", "lower tier"
        ]):
            return "VENDOR_ALTERNATIVES", None

        # 6. Spending Breakdown & Top Outflows
        if any(p in m for p in [
            "where did my money go", "where did most of my money go", "biggest expense",
            "top spending", "highest spending", "which category", "spending breakdown",
            "spending by category", "what did i spend the most on", "spending on groceries",
            "which expenses increased", "unusual spending", "how much did i spend",
            "what did i spend"
        ]):
            return "SPENDING_BREAKDOWN", None

        # 7. Budget Pacing & Health Status
        if any(p in m for p in [
            "exceeding my budget", "over budget", "budget limit", "how much budget",
            "am i over budget", "budget status", "budget remaining", "budget cushion",
            "exceeding our budget", "over our budget"
        ]):
            return "BUDGET_STATUS", None

        # 8. Affordability / Purchase Simulation
        if any(p in m for p in [
            "can i afford", "can we afford", "should we buy", "should i buy",
            "can we buy", "can i buy", "what if we buy", "what if we subscribe",
            "simulate purchase", "afford a", "afford to buy", "afford new"
        ]):
            return "AFFORDABILITY_CHECK", None

        # 9. Upcoming Renewals / Payment Calendar
        if any(p in m for p in [
            "renewal", "renewing", "upcoming payment", "next payment",
            "payment calendar", "due date", "when is my next", "next renewal",
            "payments due", "renewals next"
        ]):
            return "RENEWAL_CALENDAR", None

        # 10. Forecast / Runway / Cash Burn
        if any(p in m for p in [
            "forecast", "runway", "cash flow", "burn rate", "closing balance",
            "run out of money", "projected balance", "how long will", "cash projection",
            "how many months of cash"
        ]):
            return "FORECAST_INQUIRY", None

        # 11. Reports / Summary
        if any(p in m for p in [
            "monthly report", "report summary", "summarize report", "financial report",
            "expense report", "briefing", "executive summary", "generate report"
        ]):
            return "REPORT_SUMMARY", None

        # 12. Financial Health & Risks
        if any(p in m for p in [
            "health score", "health index", "financial health", "risks", "critical risk",
            "risk intelligence", "how healthy", "financial score"
        ]):
            return "HEALTH_AND_RISKS", None

        # 13. Recommendations & Actions
        if any(p in m for p in [
            "recommendation", "what should i do", "cfo action", "cut cost",
            "save money", "optimize spend", "action plan", "negotiate"
        ]):
            return "RECOMMENDATIONS", None

        # 14. Operating Revenue
        if any(p in m for p in [
            "operating revenue", "how much revenue", "how much money do we make",
            "monthly revenue", "sales revenue", "top line", "gross income"
        ]):
            return "REVENUE_INQUIRY", None

        # 15. Subscription Spend / Vendor Inquiry
        if any(p in m for p in [
            "subscription", "subscriptions", "spend on", "how much do i spend",
            "total software", "software cost", "vendor", "saas spend", "monthly sub",
            "recurring payment", "recurring payments"
        ]):
            return "SPEND_OVERVIEW", None

        # 16. General Finance Inquiries
        finance_keywords = [
            "money", "dollar", "cash", "finance", "financial", "ledger", "invoice",
            "payment", "bank", "fund", "balance", "income", "profit", "burn", "account"
        ]
        if any(re.search(rf"\b{w}\b", m) for w in finance_keywords):
            return "GENERAL_FINTECH", None

        # 17. Non-financial casual fallback
        return "CASUAL_CONVERSATION", "general_casual"

    @classmethod
    def detect_intent(
        cls,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Classifies incoming user question into fintech or conversational intent categories.
        """
        intent, _ = cls.classify_conversational_type(message, history=history)
        return intent

    @classmethod
    def _call_gemini_conversational(
        cls,
        message: str,
        intent: str,
        history: Optional[List[Dict[str, Any]]] = None,
        account_type: str = "business",
    ) -> Optional[str]:
        if not cls.is_llm_configured():
            return None

        api_key = (settings.GEMINI_API_KEY or settings.LLM_API_KEY or "").strip()
        if not api_key:
            return None

        if intent == "CASUAL_CONVERSATION":
            system_prompt = (
                f"You are SubWise AI, a friendly, intelligent, and human-like conversational assistant for a {account_type.capitalize()} account. "
                "You converse naturally, warmly, and concisely. "
                "CRITICAL GUIDELINES:\n"
                "1. Keep responses natural, conversational, and concise (1-3 sentences for greetings and casual remarks).\n"
                "2. Match the user's conversational tone.\n"
                "3. Do NOT use excessive emojis (at most 1 contextual emoji or none).\n"
                "4. Do NOT repeatedly introduce yourself with your full name or company unless specifically asked.\n"
                "5. Do NOT force every response into a financial lecture or pitch.\n"
                "6. Never invent fake personal financial accounts, transactions, or balances.\n"
                "7. Never claim to perform payments, fund transfers, cancellations, or ledger modifications."
            )
        else:
            system_prompt = (
                f"You are SubWise AI, an intelligent, helpful assistant for a {account_type.capitalize()} account. "
                "You explain concepts and answer general knowledge questions clearly, accurately, and concisely. "
                "CRITICAL GUIDELINES:\n"
                "1. Provide clean, clear explanations in natural language.\n"
                "2. Keep the answer educational, structured, and easy to understand.\n"
                "3. Format with clean Markdown (bullet points or bolding where appropriate).\n"
                "4. Do NOT invent fake user personal account data.\n"
                "5. Never claim to perform real-world financial payments or account mutations."
            )

        history_context = ""
        if history:
            history_context = "\n\nRECENT CONVERSATION TURNS:\n"
            for h in history[-6:]:
                r = h.get("role", "user").capitalize()
                c = h.get("content", "")
                history_context += f"{r}: {c}\n"

        full_prompt = (
            f"{system_prompt}\n"
            f"{history_context}\n"
            f"USER: {message}\n\n"
            f"ASSISTANT:"
        )

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
                        if text and text.strip():
                            return text.strip()
        except Exception:
            return None

        return None

    @classmethod
    def _generate_deterministic_casual(
        cls,
        subtype: str,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        account_type: str = "business",
    ) -> Tuple[str, List[str]]:
        clean = re.sub(r"[^\w\s]", "", message.lower()).strip()
        has_prior_assistant_turns = any(h.get("role") == "assistant" for h in (history or []))

        if subtype == "greeting":
            if not has_prior_assistant_turns:
                text = "Hey! How's it going? I'm your SubWise AI assistant. What can I help you with today?"
            else:
                text = "Hey again! What's on your mind?"
            followups = [
                "How much did I spend this month?",
                "What subscriptions am I paying for?",
                "Explain machine learning",
            ]
            return text, followups

        if subtype == "checkin":
            if any(k in clean for k in ["how are you", "how are u", "how r u"]):
                text = "I'm doing well, thank you for asking! Ready to help you analyze your finances, answer questions, or just chat. How is your day going?"
            elif any(k in clean for k in ["what are you doing", "what r u doing", "what are u doing", "what are you up to"]):
                text = "Just here and ready to help! I'm keeping track of financial insights and ready to chat about whatever is on your mind. What are you up to?"
            elif any(k in clean for k in ["what is up", "whats up", "what's up"]):
                text = "Not much! Just ready to help you explore your finances, learn something new, or have a quick chat. What's on your mind today?"
            elif any(k in clean for k in ["who are you", "what can you do", "introduce yourself", "tell me about yourself"]):
                text = (
                    "I'm SubWise AI, your conversational assistant. I can chat casually, answer general knowledge questions, "
                    "and provide in-depth financial intelligence—like tracking recurring subscriptions, calculating budgets, "
                    "forecasting cash flow, and identifying cost-saving alternatives."
                )
            else:
                text = "Everything is running smoothly! Ready for whatever questions or financial insights you have in mind. How can I help?"
            followups = [
                "Where did most of my money go this month?",
                "Can I afford a new subscription for $30/mo?",
                "Tell me something interesting",
            ]
            return text, followups

        if subtype == "appreciation":
            text = "You're very welcome! Let me know whenever you need anything else."
            followups = [
                "What are my upcoming renewals?",
                "Am I over budget?",
                "Explain compound interest",
            ]
            return text, followups

        if subtype == "farewell":
            if "night" in clean:
                text = "Good night! Rest well and see you next time."
            else:
                text = "Goodbye! Have a great day ahead, and feel free to reach out whenever you're back."
            return text, []

        if subtype == "boredom":
            if any(k in clean for k in ["bored", "im bored"]):
                text = "Let's make things interesting! Want to learn something new or just have a casual chat? We could explore an interesting concept, talk about tech, or take a quick look at your financial trends."
            elif any(k in clean for k in ["joke", "laugh"]):
                text = "Why did the computer keep freezing? Because it left its Windows open! Let me know if you want another one, or if you'd like to explore something new."
            elif any(k in clean for k in ["interesting", "fact"]):
                text = (
                    "Here's an interesting fact: The word 'salary' comes from the Latin 'salarium', which was an allowance "
                    "given to Roman soldiers to purchase salt—a prized commodity at the time. Want to hear another fun fact or dive into a topic?"
                )
            else:
                text = "I'm always up for a good conversation! We can discuss how AI works, talk about economics, or check in on your financial goals. What sounds fun?"
            followups = [
                "Tell me something interesting",
                "Explain machine learning",
                "How much did I spend this month?",
            ]
            return text, followups

        # Default general casual
        text = "I'm here and happy to chat! Whether you want to discuss everyday topics, learn something new, or dive into your financial numbers, feel free to ask."
        followups = [
            "How much did I spend this month?",
            "Explain machine learning",
            "What subscriptions do I have?",
        ]
        return text, followups

    @classmethod
    def _generate_deterministic_knowledge(
        cls,
        subtype: str,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[str, List[str]]:
        if subtype == "machine_learning":
            text = (
                "Machine learning is a type of AI that helps computers learn patterns from data and make predictions "
                "without being explicitly programmed for every task. In finance, it powers fraud detection, algorithmic analysis, "
                "credit scoring, and automated subscription anomaly detection."
            )
            followups = [
                "How is machine learning used in finance?",
                "What is the difference between AI and ML?",
                "How much did I spend this month?",
            ]
            return text, followups

        if subtype == "ai":
            text = (
                "Artificial intelligence (AI) is the broader branch of computer science dedicated to building systems "
                "capable of performing tasks that typically require human cognition—such as understanding speech, "
                "recognizing images, reasoning, and solving complex problems."
            )
            followups = [
                "Explain machine learning",
                "What is deep learning?",
                "How does SubWise AI use financial intelligence?",
            ]
            return text, followups

        if subtype == "deep_learning":
            text = (
                "Deep learning is a specialized branch of machine learning that uses multi-layered artificial neural networks. "
                "Inspired by the human brain, deep neural networks excel at recognizing complex patterns in raw data like "
                "images, audio, and large-scale language models."
            )
            followups = [
                "Explain machine learning",
                "What is artificial intelligence?",
                "How much did I spend this month?",
            ]
            return text, followups

        if subtype == "inflation":
            text = (
                "Inflation is the gradual rate at which the general prices of goods and services rise across an economy "
                "over time, which reduces the purchasing power of money. When inflation is high, every dollar buys a smaller "
                "percentage of a good or service."
            )
            followups = [
                "What is compound interest?",
                "How does inflation affect cash runway?",
                "Where can I cut costs?",
            ]
            return text, followups

        if subtype == "compound_interest":
            text = (
                "Compound interest is interest calculated on both the initial principal and the accumulated interest from "
                "previous periods. Because you earn 'interest on your interest,' compounding generates exponential growth "
                "over longer timeframes."
            )
            followups = [
                "What is inflation?",
                "What is opportunity cost?",
                "What is my cash runway?",
            ]
            return text, followups

        if subtype == "credit_score":
            text = (
                "A credit score is a numerical rating (typically ranging from 300 to 850) that indicates an individual's "
                "creditworthiness. It is calculated from on-time payment history, credit utilization, length of credit history, "
                "new credit inquiries, and credit mix."
            )
            followups = [
                "What is compound interest?",
                "Am I over budget?",
                "Where did most of my money go?",
            ]
            return text, followups

        if subtype == "cash_flow":
            text = (
                "Cash flow is the net amount of money moving into and out of an account or business over a given period. "
                "Positive cash flow occurs when cash inflows exceed outflows, while negative cash flow means expenses exceed "
                "incoming revenue."
            )
            followups = [
                "What is our projected cash runway?",
                "How much did I spend this month?",
                "What are my upcoming subscription renewals?",
            ]
            return text, followups

        if subtype == "blockchain":
            text = (
                "A blockchain is a decentralized, distributed digital ledger that securely records transactions across a network "
                "of computers. Because each block is cryptographically linked to the previous one, the records are transparent and "
                "highly resistant to retroactive tampering."
            )
            followups = [
                "What is cloud computing?",
                "Explain machine learning",
                "What are my active subscriptions?",
            ]
            return text, followups

        if subtype == "cloud_computing":
            text = (
                "Cloud computing is the on-demand delivery of computing services—such as servers, storage, databases, and "
                "software—over the internet with pay-as-you-go pricing, enabling organizations to scale resources without "
                "purchasing physical hardware."
            )
            followups = [
                "What is machine learning?",
                "Find cheaper software alternatives",
                "What are my recurring subscriptions?",
            ]
            return text, followups

        if subtype == "quantum_computing":
            text = (
                "Quantum computing uses the principles of quantum mechanics—such as superposition and entanglement—to process "
                "complex data exponentially faster than classical computers for specialized classes of problems, such as cryptography "
                "and complex molecular simulations."
            )
            followups = [
                "Explain machine learning",
                "What is artificial intelligence?",
                "Tell me something interesting",
            ]
            return text, followups

        if subtype == "opportunity_cost":
            text = (
                "Opportunity cost represents the potential benefit or value an individual or business misses out on when choosing "
                "one alternative over another. For instance, spending money on an unused subscription carries the opportunity cost "
                "of not investing those funds elsewhere."
            )
            followups = [
                "What recommendations do you have to cut costs?",
                "Where did most of my money go?",
                "Can I afford a new subscription?",
            ]
            return text, followups

        if subtype == "emergency_fund":
            text = (
                "An emergency fund is a dedicated savings reserve—typically 3 to 6 months of essential living expenses—kept in an "
                "accessible, low-risk account to cover unexpected expenses such as medical emergencies or income disruptions."
            )
            followups = [
                "What is our cash runway?",
                "Am I over budget?",
                "Where can I save money?",
            ]
            return text, followups

        if subtype == "python":
            text = (
                "Python is a high-level, interpreted programming language celebrated for its readable syntax, versatility, and "
                "rich ecosystem of open-source libraries. It is widely used in web development, automation, data analytics, and AI."
            )
            followups = [
                "Explain machine learning",
                "Tell me something interesting",
                "What can you do?",
            ]
            return text, followups

        # General concept fallback
        clean_topic = re.sub(
            r"^(explain|what is|what are|how does|how do|tell me about|define)\s+",
            "",
            message,
            flags=re.IGNORECASE
        ).strip(" ?.!").title()
        if not clean_topic:
            clean_topic = "This Concept"

        text = (
            f"**{clean_topic}** is a fundamental concept often encountered in technology, economics, or general knowledge. "
            f"It involves understanding how individual components interact within a structured framework to produce consistent results. "
            f"Let me know if you would like to explore specific aspects or applications, or feel free to ask about your financial records!"
        )
        followups = [
            "Explain machine learning",
            "How much did I spend this month?",
            "What subscriptions do I have?",
        ]
        return text, followups

    @classmethod
    def _parse_affordability_params(cls, message: str) -> Dict[str, Any]:
        """
        Extracts proposed vendor, amount, cadence, and purpose from natural language.
        Examples:
          - "Can I afford Notion for $20/month?" -> vendor='Notion', amount=20.0, cadence='monthly'
          - "Can we buy Salesforce for $300 a month?" -> vendor='Salesforce', amount=300.0, cadence='monthly'
          - "Can we afford an annual AWS tool for $1200/year?" -> vendor='AWS tool', amount=1200.0, cadence='annual'
        """
        clean_msg = message.replace(",", "")

        # Cadence detection
        cadence = "monthly"
        if re.search(r"\b(annually|annual|per year|a year|/yr|/year)\b", clean_msg, re.IGNORECASE):
            cadence = "annual"
        elif re.search(r"\b(quarterly|per quarter|a quarter|/qtr)\b", clean_msg, re.IGNORECASE):
            cadence = "quarterly"
        elif re.search(r"\b(weekly|per week|a week|/wk)\b", clean_msg, re.IGNORECASE):
            cadence = "weekly"

        # Amount extraction: $XX.XX or $XX or XX dollars or XX/mo
        amount = 0.0
        amt_match = re.search(r"\$([0-9]+(?:\.[0-9]{1,2})?)", clean_msg)
        if not amt_match:
            amt_match = re.search(r"([0-9]+(?:\.[0-9]{1,2})?)\s*(?:dollars|usd|\/mo|\/month|\/year|\/yr)", clean_msg, re.IGNORECASE)
        if not amt_match:
            amt_match = re.search(r"\bfor\s+([0-9]+(?:\.[0-9]{1,2})?)\b", clean_msg, re.IGNORECASE)

        if amt_match:
            try:
                amount = float(amt_match.group(1))
            except ValueError:
                amount = 0.0

        # Vendor extraction
        vendor = "Proposed Tool"
        vendor_match = re.search(
            r"(?:afford|buy|subscribe to|get)\s+(?:a |an |new )?([A-Za-z0-9\s\-]+?)\s+(?:for|costing|at|\$)",
            clean_msg,
            re.IGNORECASE
        )
        if vendor_match:
            candidate = vendor_match.group(1).strip()
            # clean noise
            candidate = re.sub(r"^(a|an|new|the|to|subscription|tool)\s+", "", candidate, flags=re.IGNORECASE).strip()
            if candidate and len(candidate) > 1 and len(candidate) < 40:
                vendor = candidate.title()
        else:
            # Check for words before "for $XX"
            v_match2 = re.search(r"([A-Za-z0-9\-]+)\s+for\s+\$", clean_msg, re.IGNORECASE)
            if v_match2:
                vendor = v_match2.group(1).strip().title()

        return {
            "proposed_vendor": vendor,
            "amount": amount,
            "cadence": cadence,
            "business_purpose": "Simulated via SubWise AI Assistant",
        }

    # -------------------------------------------------------------------------
    # Core Query Processing
    # -------------------------------------------------------------------------
    @classmethod
    def process_query(
        cls,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
        request: AssistantQueryRequest,
        db: Optional[Any] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> AssistantQueryResponse:
        """
        Coordinates intent classification, deterministic facts gathering,
        specialized simulation / report routing, and AI or deterministic synthesis.
        """
        message = request.message.strip()
        intent = cls.detect_intent(message, history=history)

        # 1. Fetch deterministic financial overview & ground truth facts
        overview = FinancialIntelligenceEngine.generate_overview(
            business=business,
            subscriptions=subscriptions,
            transactions=transactions,
        )
        data_status = overview.data_sufficiency_status
        hist_actuals = overview.historical_actuals
        forward_commit = overview.forward_commitments
        projected = overview.projected_estimates
        health = overview.financial_health_index
        risks = overview.risk_intelligence

        # Also get detailed forecast with calendar schedule
        forecast_data = ForecastEngine.generate_forecast(
            business=business,
            subscriptions=subscriptions,
            transactions=transactions,
            forecast_months=6,
        )

        company_name = business.company_name or "Your Account"
        disclaimer = (
            "SubWise AI is a decision-support assistant. All figures are derived strictly "
            "from connected PayPal transactions and deterministic forecasting formulas, not speculative forecasts."
        )

        # ---------------------------------------------------------------------
        # ROUTE: READ-ONLY SAFETY GUARD (Phase 9 Security Boundary)
        # ---------------------------------------------------------------------
        if intent == "READ_ONLY_GUARD":
            card = EvidenceCard(
                title="Strict Read-Only Architecture",
                data_type="informational",
                amount=None,
                currency="USD",
                details={
                    "security_policy": "Strict Read-Only Enforcement",
                    "audit_compliance": "SOC2 & PCI-DSS Audit Safe",
                    "direct_mutation_allowed": False,
                },
                navigation_link="/subscriptions",
                badge_label="Read-Only Protected",
                badge_status="neutral",
            )
            guard_md = (
                f"### 🛡️ **SubWise AI Assistant Operates in Read-Only Mode**\n\n"
                f"To protect your financial security, prevent accidental balance deductions, and maintain an immutable ledger audit trail, "
                f"the AI Assistant is architected to be **strictly read-only**.\n\n"
                f"The assistant **cannot** directly execute payments, transfer funds, alter account balances, cancel third-party subscriptions, or delete ledger records.\n\n"
                f"#### **How to perform this action directly:**\n"
                f"- **Manage Subscriptions:** Visit the [Subscriptions Page](/subscriptions) to cancel, pause, or view billing contracts.\n"
                f"- **Edit or Add Expenses:** Visit the [Expenses Page](/expenses) to adjust ledger line items or categories.\n"
                f"- **Adjust Household Settings:** Visit the [Household Page](/household) to manage members and contribution splits.\n"
                f"- **Simulate Scenarios:** Visit the [Forecast & Simulator](/forecast) to test financial changes before committing them."
            )
            actions = [
                ChatAction(label="Manage Subscriptions", path="/subscriptions", description="View active subscriptions and cancel services"),
                ChatAction(label="Manage Expenses", path="/expenses", description="View and update ledger expenses"),
                ChatAction(label="Run Simulation", path="/forecast", description="Test financial impact in cash flow simulator"),
            ]
            return AssistantQueryResponse(
                response_text=guard_md,
                is_ai_generated=False,
                generation_model="SubWise Financial Safety Guard",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What are my upcoming subscription renewals?",
                    "Where did most of my money go this month?",
                    "Can I afford a new subscription for $50/mo?",
                ],
                actions=actions,
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE: CASUAL CONVERSATION (Natural Greetings, Check-ins, Appreciation, Farewells)
        # ---------------------------------------------------------------------
        if intent == "CASUAL_CONVERSATION":
            subtype = cls._get_casual_subtype(message)
            is_llm = cls.is_llm_configured()
            if is_llm:
                ai_text = cls._call_gemini_conversational(
                    message=message,
                    intent=intent,
                    history=history,
                    account_type=business.account_type or "business",
                )
                if ai_text:
                    return AssistantQueryResponse(
                        response_text=ai_text,
                        is_ai_generated=True,
                        generation_model="Google Gemini 1.5 Flash (Conversational AI)",
                        intent=intent,
                        data_sufficiency_status=data_status,
                        evidence_cards=[],
                        suggested_followups=[
                            "How much did I spend this month?",
                            "What subscriptions am I paying for?",
                            "Explain machine learning",
                        ],
                        actions=[],
                        reporting_period=overview.monthly_briefing.reporting_period,
                        disclaimer="SubWise AI conversational assistant.",
                        llm_provider_configured=True,
                    )

            # Deterministic conversational fallback
            text, followups = cls._generate_deterministic_casual(
                subtype=subtype,
                message=message,
                history=history,
                account_type=business.account_type or "business",
            )
            return AssistantQueryResponse(
                response_text=text,
                is_ai_generated=False,
                generation_model="SubWise Conversational Intelligence Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[],
                suggested_followups=followups,
                actions=[],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer="SubWise AI conversational assistant.",
                llm_provider_configured=is_llm,
            )

        # ---------------------------------------------------------------------
        # ROUTE: GENERAL KNOWLEDGE (Educational Explanations, Concepts, General Topics)
        # ---------------------------------------------------------------------
        if intent == "GENERAL_KNOWLEDGE":
            subtype = cls._get_knowledge_subtype(message)
            is_llm = cls.is_llm_configured()
            if is_llm:
                ai_text = cls._call_gemini_conversational(
                    message=message,
                    intent=intent,
                    history=history,
                    account_type=business.account_type or "business",
                )
                if ai_text:
                    return AssistantQueryResponse(
                        response_text=ai_text,
                        is_ai_generated=True,
                        generation_model="Google Gemini 1.5 Flash (Educational & Knowledge)",
                        intent=intent,
                        data_sufficiency_status=data_status,
                        evidence_cards=[],
                        suggested_followups=[
                            "How does this apply to finance?",
                            "How much did I spend this month?",
                            "What are my active subscriptions?",
                        ],
                        actions=[],
                        reporting_period=overview.monthly_briefing.reporting_period,
                        disclaimer="SubWise AI educational knowledge mode.",
                        llm_provider_configured=True,
                    )

            # Deterministic general knowledge fallback
            text, followups = cls._generate_deterministic_knowledge(
                subtype=subtype,
                message=message,
                history=history,
            )
            return AssistantQueryResponse(
                response_text=text,
                is_ai_generated=False,
                generation_model="SubWise Conversational Intelligence Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[],
                suggested_followups=followups,
                actions=[],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer="SubWise AI educational knowledge mode.",
                llm_provider_configured=is_llm,
            )

        # ---------------------------------------------------------------------
        # ROUTE: HOUSEHOLD_SPENDING (Phase 9 Multi-Account Requirement)
        # ---------------------------------------------------------------------
        if intent == "HOUSEHOLD_SPENDING" or (business.account_type == "household" and any(k in message.lower() for k in ["member", "who spent", "household", "shared"])):
            from app.models.household_member import HouseholdMember
            from app.models.expense import Expense

            members = []
            expenses = []
            if db:
                members = db.query(HouseholdMember).filter(HouseholdMember.business_id == business.id, HouseholdMember.is_active == True).all()
                expenses = db.query(Expense).filter(Expense.business_id == business.id).all()

            member_map = {m.id: m.name for m in members}
            member_spend = {m.name: 0.0 for m in members}
            member_spend["Unassigned / Shared"] = 0.0

            total_household_spend = 0.0
            for exp in expenses:
                if exp.expense_type == "expense":
                    amt = float(exp.amount or 0.0)
                    total_household_spend += amt
                    m_name = member_map.get(exp.household_member_id, "Unassigned / Shared")
                    member_spend[m_name] = member_spend.get(m_name, 0.0) + amt

            filtered_spend = {k: v for k, v in member_spend.items() if v > 0 or k != "Unassigned / Shared"}
            if not filtered_spend:
                filtered_spend = member_spend

            top_member = max(filtered_spend.items(), key=lambda x: x[1]) if filtered_spend else ("None", 0.0)

            card = EvidenceCard(
                title="Household Member Spending",
                data_type="actual",
                amount=total_household_spend,
                currency="USD",
                details={
                    "total_household_spend": total_household_spend,
                    "members_count": len(members),
                    "top_spender": top_member[0],
                    "top_spender_amount": top_member[1],
                    "member_breakdown": filtered_spend,
                },
                navigation_link="/household",
                badge_label=f"${total_household_spend:,.2f} Total",
                badge_status="info",
            )

            h_md = (
                f"### Household Spending & Member Allocation\n\n"
                f"- **Total Recorded Household Spend:** **${total_household_spend:,.2f}**\n"
                f"- **Active Household Members:** {len(members)}\n"
            )
            if top_member[1] > 0:
                h_md += f"- **Highest Outflow Contribution:** **{top_member[0]}** (${top_member[1]:,.2f})\n\n"

            if members or expenses:
                h_md += "**Member Spending Breakdown:**\n\n| Member | Total Spent | Share |\n| :--- | :--- | :--- |\n"
                for m_name, s_amt in sorted(filtered_spend.items(), key=lambda x: x[1], reverse=True):
                    share_pct = (s_amt / total_household_spend * 100) if total_household_spend > 0 else 0.0
                    h_md += f"| **{m_name}** | ${s_amt:,.2f} | {share_pct:.1f}% |\n"

            h_md += "\nManage members, budget caps, and contribution splits on the [Household Dashboard](/household)."

            return AssistantQueryResponse(
                response_text=h_md,
                is_ai_generated=False,
                generation_model="SubWise Household Allocation Engine",
                intent="HOUSEHOLD_SPENDING",
                data_sufficiency_status="sufficient_data" if expenses else "limited_data",
                evidence_cards=[card],
                suggested_followups=[
                    "Are we on track with our household monthly budget?",
                    "Where can our household cut costs to save $150/month?",
                    "What shared recurring subscriptions are active?",
                ],
                actions=[
                    ChatAction(label="Household Dashboard", path="/household", description="View household members and contributions"),
                    ChatAction(label="Shared Expenses", path="/expenses", description="View all household expenses"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE: CONTEXTUAL FOLLOW-UP (Phase 9 Contextual Memory)
        # ---------------------------------------------------------------------
        if intent == "CONTEXTUAL_FOLLOWUP":
            # 1. Prior billing cycle comparison
            is_financial_month = any(k in message.lower() for k in ["last month", "previous month", "prior month", "last billing", "prior cycle"])

            # 2. Check if immediately preceding user question was general knowledge
            prev_was_knowledge = False
            last_knowledge_topic = ""
            if not is_financial_month and history:
                immediate_user_msg = ""
                for h in reversed(history):
                    if h.get("role") == "user":
                        immediate_user_msg = h.get("content", "").lower()
                        break

                if immediate_user_msg:
                    for topic in ["machine learning", "artificial intelligence", "deep learning", "inflation", "compound interest", "credit score", "blockchain", "quantum computing"]:
                        if topic in immediate_user_msg:
                            prev_was_knowledge = True
                            last_knowledge_topic = topic
                            break

            if prev_was_knowledge:
                is_llm = cls.is_llm_configured()
                if is_llm:
                    ai_text = cls._call_gemini_conversational(
                        message=message,
                        intent="GENERAL_KNOWLEDGE",
                        history=history,
                        account_type=business.account_type or "business",
                    )
                    if ai_text:
                        return AssistantQueryResponse(
                            response_text=ai_text,
                            is_ai_generated=True,
                            generation_model="Google Gemini 1.5 Flash (Educational Follow-up)",
                            intent="CONTEXTUAL_FOLLOWUP",
                            data_sufficiency_status=data_status,
                            evidence_cards=[],
                            suggested_followups=[
                                "How does this apply to finance?",
                                "How much did I spend this month?",
                                "What are my active subscriptions?",
                            ],
                            actions=[],
                            reporting_period=overview.monthly_briefing.reporting_period,
                            disclaimer="SubWise AI educational knowledge mode.",
                            llm_provider_configured=True,
                        )

                # Deterministic knowledge follow-up
                if last_knowledge_topic == "machine learning":
                    kf_text = (
                        "Machine learning algorithms learn by evaluating training examples against a mathematical loss function. "
                        "They iteratively update internal weights through optimization methods (like gradient descent), allowing the model "
                        "to minimize errors and discover patterns directly from raw data without needing hardcoded rules."
                    )
                elif last_knowledge_topic == "inflation":
                    kf_text = (
                        "Inflation typically accelerates when total aggregate demand in an economy outpaces production capacity ('demand-pull'), "
                        "or when input costs like labor and energy spike ('cost-push'). Central banks adjust interest rates to manage this balance."
                    )
                elif last_knowledge_topic == "compound interest":
                    kf_text = (
                        "The mathematical formula for compound interest is A = P(1 + r/n)^(nt), where P is the principal, r is the annual rate, "
                        "n is compounding frequency, and t is time. Because exponentiation compounds over time, starting early provides outsized benefits."
                    )
                else:
                    kf_text = (
                        f"Building on {last_knowledge_topic.title()}, continuous learning and observation allow structured models "
                        "to adapt to evolving data inputs over time. Let me know if you would like to explore practical examples or connect this to your financial data!"
                    )

                return AssistantQueryResponse(
                    response_text=kf_text,
                    is_ai_generated=False,
                    generation_model="SubWise Conversational Intelligence Engine",
                    intent=intent,
                    data_sufficiency_status=data_status,
                    evidence_cards=[],
                    suggested_followups=[
                        "How much did I spend this month?",
                        "What are my active subscriptions?",
                        "Can I afford a new subscription for $30/mo?",
                    ],
                    actions=[],
                    reporting_period=overview.monthly_briefing.reporting_period,
                    disclaimer="SubWise AI contextual follow-up mode.",
                    llm_provider_configured=is_llm,
                )

            # Financial Contextual Follow-up (Prior month comparison or financial driver analysis)
            if any(k in message.lower() for k in ["last month", "previous month", "prior month"]):
                cf_md = (
                    f"### Historical Comparison & Previous Month Context for **{company_name}**\n\n"
                    f"Comparing current operating data against the prior billing cycle:\n\n"
                    f"- **Historical Revenue Baseline:** ${hist_actuals.historical_monthly_operating_revenue:,.2f}/mo\n"
                    f"- **Historical Operating Outflows:** ${hist_actuals.historical_monthly_operating_expenses:,.2f}/mo\n"
                    f"- **Recurring Subscription Commitments:** ${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo\n\n"
                    f"For an itemized month-by-month comparative ledger, view the [Reports Page](/reports) or review category spikes on [Expenses](/expenses)."
                )
            else:
                cf_md = (
                    f"### Contextual Financial Analysis for **{company_name}**\n\n"
                    f"Following up on our financial review:\n\n"
                    f"- **Confirmed Subscription Commitments:** ${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo\n"
                    f"- **Current Net Monthly Cash Flow:** ${hist_actuals.historical_monthly_net_cash_flow:,.2f}/mo\n"
                    f"- **Liquid Cash Reserves:** ${hist_actuals.verified_available_cash or 0.0:,.2f}\n\n"
                    f"Outflow changes are primarily driven by active recurring commitments, billing cadence synchronizations, or variable discretionary transactions."
                )

            card = EvidenceCard(
                title="Contextual Analysis",
                data_type="actual",
                amount=hist_actuals.historical_monthly_operating_expenses,
                currency="USD",
                details={
                    "operating_months": hist_actuals.operating_months_analyzed,
                    "monthly_operating_outflows": hist_actuals.historical_monthly_operating_expenses,
                },
                navigation_link="/reports",
                badge_label="Contextual Context",
                badge_status="neutral",
            )
            return AssistantQueryResponse(
                response_text=cf_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Intelligence Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "Where did most of my money go this month?",
                    "What are our upcoming subscription renewals?",
                    "What is our projected cash runway?",
                ],
                actions=[
                    ChatAction(label="Financial Reports", path="/reports", description="Month-by-month financial ledger"),
                    ChatAction(label="Expenses Page", path="/expenses", description="View itemized category transactions"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 0A: VENDOR & ALTERNATIVE COMPARISON (Phase 4 AI Discovery)
        # ---------------------------------------------------------------------
        if intent == "VENDOR_ALTERNATIVES":
            matched = VendorComparisonService.search_alternatives(message)
            total_est_save = sum(item.recommended_alternative.estimated_monthly_savings for item in matched)

            card = EvidenceCard(
                title="Vendor Alternative Savings",
                data_type="projected",
                amount=total_est_save,
                currency="USD",
                details={
                    "alternatives_count": len(matched),
                    "annual_savings_potential": total_est_save * 12,
                    "top_match": matched[0].current_service_name if matched else "None",
                },
                navigation_link="/recommendations",
                badge_label=f"Save up to ${total_est_save:.2f}/mo",
                badge_status="success",
            )

            res_md = (
                f"### Economical Vendor Alternatives & Savings Analysis\n\n"
                f"Based on verified Q4 2026 pricing benchmarks, here are high-value alternatives for your recurring expenses:\n\n"
            )

            for item in matched[:3]:
                alt = item.recommended_alternative
                res_md += (
                    f"#### 🔍 **{item.current_service_name}** ({item.category})\n"
                    f"- **Current Reference Tier:** {item.current_tier} at **${item.current_price:.2f}/{item.current_frequency}**\n"
                    f"- **Recommended Alternative:** **{alt.name} — {alt.tier}** at **${alt.price:.2f}/{alt.billing_frequency}** (${alt.monthly_equivalent:.2f}/mo equivalent)\n"
                    f"- **Estimated Monthly Recapture:** **${alt.estimated_monthly_savings:.2f}/mo** (${alt.estimated_annual_savings:.2f}/year)\n"
                    f"- **Trade-offs / Caveats:** {'; '.join(alt.trade_offs)}\n\n"
                )

            res_md += f"> 💡 **Actionable Verdict:** Switching these services frees up an estimated **${total_est_save:.2f}/month** (${total_est_save * 12:.2f}/year) without sacrificing essential capabilities. Review the full catalog in [Savings Opportunities](/recommendations)."

            return AssistantQueryResponse(
                response_text=res_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Vendor Discovery Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "Where did most of my money go this month?",
                    "How can I save $100 monthly?",
                    "What are my upcoming renewals?",
                ],
                actions=[
                    ChatAction(label="Savings Discovery", path="/savings-discovery", description="Explore cheaper vendor alternatives"),
                    ChatAction(label="CFO Recommendations", path="/recommendations", description="View actionable savings steps"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 0B: SPENDING BREAKDOWN & TOP OUTFLOWS
        # ---------------------------------------------------------------------
        if intent == "SPENDING_BREAKDOWN":
            category_breakdown = {}
            total_exp = hist_actuals.historical_monthly_operating_expenses
            sub_exp = forward_commit.confirmed_monthly_subscription_commitments

            if db and business.account_type in ("individual", "household"):
                from app.models.expense import Expense
                db_expenses = db.query(Expense).filter(Expense.business_id == business.id, Expense.expense_type == "expense").all()
                if db_expenses:
                    total_exp = float(sum(e.amount for e in db_expenses))
                    for e in db_expenses:
                        cat = e.category or "Other"
                        category_breakdown[cat] = category_breakdown.get(cat, 0.0) + float(e.amount or 0.0)

            card = EvidenceCard(
                title="Monthly Outflow Breakdown",
                data_type="actual",
                amount=total_exp,
                currency="USD",
                details={
                    "total_expenses": total_exp,
                    "subscription_expenses": sub_exp,
                    "discretionary_expenses": max(0.0, total_exp - sub_exp),
                    "category_breakdown": category_breakdown,
                },
                navigation_link="/expenses",
                badge_label=f"${total_exp:,.2f} Total",
                badge_status="neutral",
            )

            sb_md = (
                f"### Spending Analysis & Outflow Allocation for **{company_name}**\n\n"
                f"- **Total Recorded Outflows:** **${total_exp:,.2f}**\n"
            )
            if sub_exp > 0:
                sb_md += f"- **Confirmed Recurring Subscriptions:** **${sub_exp:,.2f}/mo** ({(sub_exp / total_exp * 100) if total_exp > 0 else 0:.1f}% of outflows)\n"

            if category_breakdown:
                top_cat = max(category_breakdown.items(), key=lambda x: x[1])
                sb_md += f"- **Top Spending Category:** **{top_cat[0]}** (${top_cat[1]:,.2f})\n\n"
                sb_md += "**Spending by Category:**\n\n| Category | Amount | Share |\n| :--- | :--- | :--- |\n"
                for cat_name, cat_amt in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True):
                    share = (cat_amt / total_exp * 100) if total_exp > 0 else 0.0
                    sb_md += f"| **{cat_name}** | ${cat_amt:,.2f} | {share:.1f}% |\n"
            elif subscriptions:
                top_subs = sorted(subscriptions, key=lambda s: float(getattr(s, 'latest_amount', 0.0) or 0.0), reverse=True)[:5]
                sb_md += "\n**Top Recurring Commitments:**\n\n| Service | Amount | Cadence |\n| :--- | :--- | :--- |\n"
                for s in top_subs:
                    sb_md += f"| **{s.vendor_name}** | ${float(getattr(s, 'latest_amount', 0.0) or 0.0):.2f} | {s.cadence or 'monthly'} |\n"

            sb_md += "\nView detailed category charts and historical trends on the [Expenses Page](/expenses)."

            return AssistantQueryResponse(
                response_text=sb_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Spending Intelligence",
                intent=intent,
                data_sufficiency_status=data_status if total_exp > 0 else "insufficient_data",
                evidence_cards=[card],
                suggested_followups=[
                    "Find cheaper alternatives for my subscriptions",
                    "Am I exceeding my monthly budget?",
                    "What is my financial health score?",
                ],
                actions=[
                    ChatAction(label="View Expenses", path="/expenses", description="Explore itemized expenses"),
                    ChatAction(label="Savings Discovery", path="/savings-discovery", description="Explore savings"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 0C: BUDGET PACING & HEALTH
        # ---------------------------------------------------------------------
        if intent == "BUDGET_STATUS":
            budget_limit = 0.0
            budget_source = "Not Configured"
            if db:
                from app.models.budget import Budget
                budgets = db.query(Budget).filter(Budget.business_id == business.id).all()
                if budgets:
                    overall_b = next((b for b in budgets if b.category.lower() == "overall"), None)
                    if overall_b and overall_b.monthly_limit > 0:
                        budget_limit = float(overall_b.monthly_limit)
                        budget_source = "Configured Overall Budget"
                    else:
                        budget_limit = float(sum(b.monthly_limit for b in budgets if b.monthly_limit > 0))
                        budget_source = "Sum of Category Budgets"

            if budget_limit == 0.0 and business.monthly_baseline_revenue and float(business.monthly_baseline_revenue) > 0:
                budget_limit = float(business.monthly_baseline_revenue)
                budget_source = "Monthly Baseline Revenue Target"

            spent = hist_actuals.historical_monthly_operating_expenses
            if spent == 0.0 and db:
                from app.models.expense import Expense
                db_exp_sum = db.query(Expense).filter(Expense.business_id == business.id, Expense.expense_type == "expense").all()
                if db_exp_sum:
                    spent = float(sum(e.amount for e in db_exp_sum))

            if budget_limit <= 0.0:
                card = EvidenceCard(
                    title="Budget Utilization",
                    data_type="informational",
                    amount=spent,
                    currency="USD",
                    details={"spent_so_far": spent, "budget_limit": "Unset"},
                    navigation_link="/expenses",
                    badge_label="Budget Unset",
                    badge_status="neutral",
                )
                b_md = (
                    f"### Budget Status: **No Budget Target Configured**\n\n"
                    f"- **Current Recorded Outflows:** **${spent:,.2f}**\n"
                    f"- **Target Monthly Budget Ceiling:** Not yet set\n\n"
                    f"You have not configured a monthly budget limit for **{company_name}**. "
                    f"To track spending pacing and receive real-time overage warnings, configure your target budget on the [Budget Manager](/expenses)."
                )
                return AssistantQueryResponse(
                    response_text=b_md,
                    is_ai_generated=False,
                    generation_model="SubWise Deterministic Budget Engine",
                    intent=intent,
                    data_sufficiency_status="limited_data",
                    evidence_cards=[card],
                    suggested_followups=[
                        "Where did most of my money go this month?",
                        "What subscriptions am I paying for?",
                        "How can I save $100 monthly?",
                    ],
                    actions=[ChatAction(label="Set Budget Target", path="/expenses", description="Set monthly spending limit")],
                    reporting_period=overview.monthly_briefing.reporting_period,
                    disclaimer=disclaimer,
                )

            rem = budget_limit - spent
            pct = (spent / budget_limit * 100) if budget_limit > 0 else 0.0

            card = EvidenceCard(
                title="Budget Utilization",
                data_type="actual",
                amount=spent,
                currency="USD",
                details={
                    "monthly_limit": budget_limit,
                    "remaining_amount": rem,
                    "utilization_percent": pct,
                    "budget_source": budget_source,
                },
                navigation_link="/expenses",
                badge_label=f"{pct:.1f}% Used",
                badge_status="success" if pct <= 85 else ("warning" if pct <= 100 else "danger"),
            )

            status_str = "Within Budget" if rem >= 0 else "Over Budget"
            b_md = (
                f"### Budget Pacing Status: **{status_str}**\n\n"
                f"- **Target Monthly Budget Limit:** **${budget_limit:,.2f}** ({budget_source})\n"
                f"- **Current Month Expenses:** **${spent:,.2f}** ({pct:.1f}% consumed)\n"
                f"- **Remaining Financial Cushion:** **${rem:,.2f}**\n\n"
            )

            if rem >= 0:
                b_md += f"> ✅ You have a **${rem:,.2f}** safety cushion remaining for this billing cycle.\n\n"
            else:
                b_md += f"> ⚠️ Outflows exceed your monthly target ceiling by **${abs(rem):,.2f}**. Consider trimming non-essential subscriptions or variable expenses.\n\n"

            b_md += "Manage individual category limits on the [Budget Manager](/expenses)."

            return AssistantQueryResponse(
                response_text=b_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Budget Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "Where did most of my money go this month?",
                    "Find cheaper alternatives for subscriptions",
                    "What is our projected cash runway?",
                ],
                actions=[
                    ChatAction(label="Manage Budgets", path="/expenses", description="Adjust spending limits"),
                    ChatAction(label="Spending Analytics", path="/reports", description="Review category trends"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 1: AFFORDABILITY CHECK (SIMULATION)
        # ---------------------------------------------------------------------
        if intent == "AFFORDABILITY_CHECK":
            params = cls._parse_affordability_params(message)
            if params["amount"] <= 0.0:
                return AssistantQueryResponse(
                    response_text=(
                        f"I can evaluate whether {company_name} can afford a new subscription, but I couldn't "
                        f"detect a valid dollar amount in your question. \n\n"
                        f"**Try asking in this format:**\n"
                        f"- *'Can I afford Notion for $20/month?'*\n"
                        f"- *'Can we buy an annual Salesforce license for $1,200/year?'*"
                    ),
                    is_ai_generated=False,
                    generation_model="SubWise Deterministic Intelligence Engine",
                    intent=intent,
                    data_sufficiency_status=data_status,
                    evidence_cards=[],
                    suggested_followups=[
                        "Can I afford a new tool for $50/month?",
                        "What is our projected cash runway?",
                    ],
                    reporting_period=overview.monthly_briefing.reporting_period,
                    disclaimer=disclaimer,
                )

            # Call RecommendationEngine.simulate_purchase deterministically
            sim_req = PurchaseSimulationRequest(
                proposed_vendor=params["proposed_vendor"],
                amount=params["amount"],
                cadence=params["cadence"],
                business_purpose=params["business_purpose"],
            )
            sim_res = RecommendationEngine.simulate_purchase(
                business=business,
                subscriptions=subscriptions,
                transactions=transactions,
                request=sim_req,
            )

            # Format evidence cards
            badge_map = {
                "success": "success",
                "warning": "warning",
                "danger": "danger",
                "neutral": "neutral"
            }
            ev_card = EvidenceCard(
                title=f"Purchase Simulation: {sim_res.proposed_vendor}",
                data_type="simulation",
                amount=sim_res.monthly_equivalent_cost,
                currency="USD",
                details={
                    "cadence": sim_res.cadence,
                    "immediate_cash_impact": sim_res.immediate_cash_impact,
                    "annual_cost": sim_res.annual_cost,
                    "verdict": sim_res.verdict,
                    "current_monthly_burn": sim_res.current_monthly_burn,
                    "simulated_monthly_burn": sim_res.simulated_monthly_burn,
                    "shortfall_detected": sim_res.projected_shortfall_detected,
                    "shortfall_month": sim_res.shortfall_month,
                },
                navigation_link="/recommendations",
                badge_label=sim_res.verdict,
                badge_status=badge_map.get(sim_res.verdict_badge, "neutral"),
            )

            response_md = (
                f"### Purchase Simulation Analysis for **{sim_res.proposed_vendor}**\n\n"
                f"**Verdict:** `{sim_res.verdict}`\n\n"
                f"{sim_res.verdict_explanation}\n\n"
                f"**Financial Impact Details:**\n"
                f"- **Proposed Cost:** ${sim_res.amount:,.2f} ({sim_res.cadence})\n"
                f"- **Monthly Equivalent:** ${sim_res.monthly_equivalent_cost:,.2f}/mo\n"
                f"- **Annual Obligation:** ${sim_res.annual_cost:,.2f}/yr\n"
                f"- **Immediate Cash Outflow:** ${sim_res.immediate_cash_impact:,.2f}\n"
                f"- **Monthly Burn Change:** ${sim_res.current_monthly_burn:,.2f}/mo → **${sim_res.simulated_monthly_burn:,.2f}/mo**\n"
            )
            if sim_res.projected_shortfall_detected and sim_res.shortfall_month:
                response_md += f"\n> ⚠️ **Liquidity Warning:** This purchase triggers a projected cash deficit in **{sim_res.shortfall_month}**.\n\n"
            elif sim_res.renewal_concentration_effect:
                response_md += f"\n- **Calendar Concentration:** {sim_res.renewal_concentration_effect}\n"

            if sim_res.action_advice:
                response_md += "\n**Recommended Action Steps:**\n" + "\n".join(f"- {a}" for a in sim_res.action_advice[:3])

            return AssistantQueryResponse(
                response_text=response_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Purchase Simulator",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[ev_card],
                suggested_followups=[
                    f"What if we pay {sim_res.proposed_vendor} annually instead?",
                    "What is our projected cash runway right now?",
                    "Show my upcoming renewals for the next 30 days",
                ],
                actions=[
                    ChatAction(label="Run In Simulator", path="/forecast", description="Test purchase impact on cash runway"),
                    ChatAction(label="Active Subscriptions", path="/subscriptions", description="Compare against existing software"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 2: REPORT SUMMARY
        # ---------------------------------------------------------------------
        if intent == "REPORT_SUMMARY":
            rep = ReportEngine.generate_monthly_financial_report(
                business=business,
                subscriptions=subscriptions,
                transactions=transactions,
                period_preset="all"
            )

            rep_card = EvidenceCard(
                title=f"Monthly Financial Report ({rep.reporting_period})",
                data_type="actual",
                amount=rep.net_operating_cashflow,
                currency="USD",
                details={
                    "total_operating_revenue": rep.total_operating_revenue,
                    "total_operating_expenses": rep.total_operating_expenses,
                    "confirmed_subscription_expenses": rep.total_confirmed_sub_expenses,
                    "verified_available_cash": rep.verified_available_cash,
                    "data_sufficiency_status": rep.data_sufficiency_status,
                },
                navigation_link="/reports",
                badge_label=f"Net: ${rep.net_operating_cashflow:,.2f}",
                badge_status="success" if rep.net_operating_cashflow >= 0 else "danger",
            )

            rep_md = (
                f"### Executive Report Summary: **{company_name}**\n"
                f"**Reporting Period:** {rep.reporting_period} | **Status:** `{rep.data_sufficiency_status.replace('_', ' ').title()}`\n\n"
                f"- **Verified Operating Revenue:** ${rep.total_operating_revenue:,.2f}\n"
                f"- **Non-Subscription Operating Outlays:** ${rep.total_non_sub_expenses:,.2f}\n"
                f"- **Confirmed Recurring Subscriptions:** ${rep.total_confirmed_sub_expenses:,.2f}\n"
                f"- **Total Operating Outflows:** ${rep.total_operating_expenses:,.2f}\n"
                f"- **Net Operating Cash Flow:** **${rep.net_operating_cashflow:,.2f}**\n\n"
                f"**Cash Reserves & Provenance:**\n"
                f"{rep.cash_provenance}\n\n"
                f"You can view and export detailed monthly breakdowns, subscription audit schedules, "
                f"and PDF reports on the [Reports Page](/reports)."
            )

            return AssistantQueryResponse(
                response_text=rep_md,
                is_ai_generated=False,
                generation_model="SubWise Report Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[rep_card],
                suggested_followups=[
                    "What are my upcoming renewals for the next 60 days?",
                    "What are our top subscription expenses?",
                    "What is our financial health score?",
                ],
                actions=[
                    ChatAction(label="Executive Report", path="/reports", description="View full financial statements"),
                    ChatAction(label="Spending Outflows", path="/expenses", description="View itemized category transactions"),
                ],
                reporting_period=rep.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 3: RENEWAL CALENDAR & UPCOMING PAYMENTS
        # ---------------------------------------------------------------------
        if intent == "RENEWAL_CALENDAR":
            upcoming = forecast_data.get("upcoming_subscription_payments", [])
            monthly_sched = forecast_data.get("monthly_scheduled_subscription_totals", [])

            # Filter next 60 days
            now = datetime.date.today()
            horizon = now + datetime.timedelta(days=60)
            next_60_payments = []
            for p in upcoming:
                p_date_str = p.get("expected_payment_date")
                if p_date_str:
                    try:
                        p_date = datetime.date.fromisoformat(p_date_str)
                        if now <= p_date <= horizon:
                            next_60_payments.append(p)
                    except ValueError:
                        next_60_payments.append(p)

            total_next_60 = sum(float(p.get("expected_amount", 0.0)) for p in next_60_payments)
            card = EvidenceCard(
                title="Upcoming Renewals (Next 60 Days)",
                data_type="contractual",
                amount=total_next_60,
                currency="USD",
                details={
                    "renewals_count": len(next_60_payments),
                    "total_upcoming_amount": total_next_60,
                },
                navigation_link="/forecast",
                badge_label=f"{len(next_60_payments)} renewals due",
                badge_status="warning" if len(next_60_payments) > 0 else "neutral",
            )

            if not upcoming:
                cal_md = (
                    f"### Upcoming Subscription Renewals\n\n"
                    f"There are **no upcoming subscription renewals** currently scheduled in your payment calendar. \n\n"
                    f"**Why?** "
                    + (
                        "Your connected PayPal Sandbox account currently has 0 active recurring subscriptions identified in the transaction ledger. "
                        if data_status == "insufficient_data" else
                        "All active subscriptions have been processed or lack future billing dates."
                    )
                    + "\n\nAs soon as recurring vendor disbursements are detected or active subscriptions are synced, "
                    "their renewal dates and expected amounts will be plotted here."
                )
            else:
                cal_md = (
                    f"### Upcoming Subscription Renewals (Next 60 Days)\n\n"
                    f"Tracking **{len(next_60_payments)} contractual renewal(s)** totaling **${total_next_60:,.2f}** over the next 60 days:\n\n"
                    f"| Vendor | Expected Date | Expected Amount | Cadence | Status |\n"
                    f"| :--- | :--- | :--- | :--- | :--- |\n"
                )
                for p in next_60_payments[:8]:
                    cal_md += f"| **{p.get('vendor_name')}** | {p.get('expected_payment_date')} | ${float(p.get('expected_amount', 0)):,.2f} {p.get('currency', 'USD')} | {p.get('billing_frequency')} | `{p.get('is_confirmed') and 'Confirmed' or 'Potential'}` |\n"

                if len(next_60_payments) > 8:
                    cal_md += f"\n*...and {len(next_60_payments) - 8} more renewals.* View the full schedule on the [Payment Calendar](/forecast).\n"

            return AssistantQueryResponse(
                response_text=cal_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Payment Calendar",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What is our projected cash runway?",
                    "Can we afford a new subscription for $50/mo?",
                    "What are our largest recurring vendors?",
                ],
                actions=[
                    ChatAction(label="Payment Calendar", path="/forecast", description="View calendar schedule of renewals"),
                    ChatAction(label="Manage Subscriptions", path="/subscriptions", description="Review all subscriptions"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 4: FORECAST & RUNWAY INQUIRY
        # ---------------------------------------------------------------------
        if intent == "FORECAST_INQUIRY":
            runway_str = f"{projected.estimated_runway_months:.1f} months" if projected.estimated_runway_months is not None else "Indeterminate"
            burn = (hist_actuals.historical_monthly_non_sub_expenses + forward_commit.confirmed_monthly_subscription_commitments) - hist_actuals.historical_monthly_operating_revenue

            card = EvidenceCard(
                title="Projected Cash Runway",
                data_type="projected",
                amount=projected.estimated_runway_months,
                currency="Months",
                details={
                    "runway_status": projected.runway_status,
                    "verified_cash": hist_actuals.verified_available_cash,
                    "monthly_revenue_baseline": projected.projected_monthly_revenue_baseline,
                    "monthly_net_cashflow": projected.projected_monthly_net_cash_flow,
                    "projected_shortfall_month": projected.projected_shortfall_month,
                },
                navigation_link="/forecast",
                badge_label=runway_str,
                badge_status="success" if (projected.estimated_runway_months or 0) >= 6 else ("warning" if (projected.estimated_runway_months or 0) >= 3 else "danger"),
            )

            if data_status == "insufficient_data":
                fc_md = (
                    f"### Cash Flow Forecast & Runway Analysis\n\n"
                    f"**Runway Status:** `Indeterminate (Insufficient Operating History)`\n\n"
                    f"We cannot calculate a cash runway or 6-month forecast for **{company_name}** because the connected "
                    f"PayPal account lacks verified customer operating revenues and regular operating disbursements.\n\n"
                    f"- **Verified Liquid Cash:** ${hist_actuals.verified_available_cash or 0.0:,.2f} ({hist_actuals.cash_provenance})\n"
                    f"- **Monthly Net Burn:** $0.00/mo\n\n"
                    f"Once customer sales transactions settle in your PayPal account, our multi-scenario engine "
                    f"(Optimistic, Baseline, Conservative) will dynamically project month-by-month cash balances."
                )
            else:
                fc_md = (
                    f"### Cash Flow Forecast & Runway Analysis for **{company_name}**\n\n"
                    f"- **Estimated Cash Runway:** **{runway_str}** (`{projected.runway_status}`)\n"
                    f"- **Available Liquid Cash:** ${hist_actuals.verified_available_cash:,.2f} ({hist_actuals.cash_provenance})\n"
                    f"- **Baseline Monthly Revenue:** ${projected.projected_monthly_revenue_baseline:,.2f}/mo\n"
                    f"- **Monthly Net Operating Cash Flow:** ${projected.projected_monthly_net_cash_flow:,.2f}/mo\n"
                )
                if projected.projected_shortfall_month:
                    fc_md += f"\n> ⚠️ **Projected Liquidity Deficit:** Under baseline assumptions, cash reserves may deplete in **{projected.projected_shortfall_month}**.\n\n"
                else:
                    fc_md += "\n> ✅ **Liquidity Solvency:** Cash reserves remain positive throughout the entire 6-month forecast horizon.\n\n"

                fc_md += f"{projected.runway_explanation}\n\nExplore detailed Optimistic (+15%) and Conservative (-20%) scenarios on the [Cash Flow Forecast Page](/forecast)."

            return AssistantQueryResponse(
                response_text=fc_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Forecast Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "Can we afford a new tool for $100/month?",
                    "What are our upcoming renewals next month?",
                    "How can we cut subscription costs?",
                ],
                actions=[
                    ChatAction(label="Forecast Scenarios", path="/forecast", description="Test optimistic and conservative models"),
                    ChatAction(label="Financial Reports", path="/reports", description="Review historical cash flow"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 5: FINANCIAL HEALTH & RISKS
        # ---------------------------------------------------------------------
        if intent == "HEALTH_AND_RISKS":
            score_label = f"{health.score}/100" if health.score is not None else "N/A"
            card = EvidenceCard(
                title="Financial Health Index",
                data_type="actual",
                amount=float(health.score) if health.score is not None else None,
                currency="Points",
                details={
                    "status_label": health.status_label,
                    "risks_detected": len(risks),
                    "scoring_methodology": health.scoring_methodology,
                },
                navigation_link="/financial-intelligence",
                badge_label=health.status_label,
                badge_status="success" if (health.score or 0) >= 70 else ("warning" if (health.score or 0) >= 45 else "danger"),
            )

            if data_status == "insufficient_data":
                h_md = (
                    f"### Financial Health & Risk Assessment\n\n"
                    f"**Health Score:** `Unestablished (Score Withheld)`\n\n"
                    f"Under SubWise AI governance standards, a financial health score is never fabricated when ledger records are insufficient. "
                    f"The connected account currently has no confirmed subscription commitments or customer revenue.\n\n"
                    f"**Identified Risk Factor:**\n"
                    f"- **Data Visibility:** Inability to project cash runway due to absence of customer receipts and recurring vendor outflows."
                )
            else:
                h_md = (
                    f"### Financial Health & Risk Assessment for **{company_name}**\n\n"
                    f"**Financial Health Score:** **{score_label}** (`{health.status_label}`)\n\n"
                    f"**Methodology:** Evaluates subscription burden vs revenue (30%), cash runway & burn buffer (35%), "
                    f"calendar renewal concentration (20%), and price creep stability (15%).\n\n"
                )
                if risks:
                    h_md += f"**Critical Financial Risks Detected ({len(risks)}):**\n"
                    for r in risks[:4]:
                        h_md += f"- **{r.title}** (`{r.severity.upper()}`): {r.description} *Evidence: {r.supporting_evidence}*\n"
                else:
                    h_md += "> ✅ **No Critical Financial Risks Detected:** Current subscription commitments and burn rates are within standard operating thresholds.\n"

            return AssistantQueryResponse(
                response_text=h_md,
                is_ai_generated=False,
                generation_model="SubWise Financial Intelligence Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What recommendations do you have to improve our score?",
                    "What are our upcoming subscription renewals?",
                    "What is our projected cash runway?",
                ],
                actions=[
                    ChatAction(label="Risk Intelligence", path="/reports", description="Inspect detailed score drivers"),
                    ChatAction(label="Actionable Insights", path="/recommendations", description="View savings recommendations"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 6: RECOMMENDATIONS
        # ---------------------------------------------------------------------
        if intent == "RECOMMENDATIONS":
            recs = RecommendationEngine.generate_recommendations(
                business=business,
                subscriptions=subscriptions,
                transactions=transactions,
            )
            card = EvidenceCard(
                title="Actionable CFO Recommendations",
                data_type="actual",
                amount=sum(r.potential_monthly_saving for r in recs),
                currency="USD",
                details={
                    "recommendations_count": len(recs),
                    "total_potential_monthly_savings": sum(r.potential_monthly_saving for r in recs),
                    "total_potential_annual_savings": sum(r.potential_annual_saving for r in recs),
                },
                navigation_link="/recommendations",
                badge_label=f"{len(recs)} actions identified",
                badge_status="info",
            )

            rec_md = f"### CFO Recommendations for **{company_name}**\n\n"
            if not recs:
                rec_md += (
                    "No immediate optimization actions required at this time. "
                    "Your subscriptions show consistent billing cadences with no identified duplicate seats or pricing creep.\n"
                )
            else:
                rec_md += f"We identified **{len(recs)} optimization action(s)**:\n\n"
                for r in recs[:5]:
                    rec_md += (
                        f"#### {r.title}\n"
                        f"- **Vendor:** {r.vendor_name or 'General Portfolio'}\n"
                        f"- **Rationale:** {r.rationale}\n"
                        f"- **Potential Savings:** ${r.potential_monthly_saving:,.2f}/mo (${r.potential_annual_saving:,.2f}/yr)\n"
                    )
                    if r.action_plan:
                        rec_md += f"- **Action Plan:** {r.action_plan}\n"
                    rec_md += "\n"

            rec_md += "\nReview details and track applied optimizations on the [Recommendations Page](/recommendations)."

            return AssistantQueryResponse(
                response_text=rec_md,
                is_ai_generated=False,
                generation_model="SubWise Recommendation Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What is our financial health score?",
                    "Can we afford a new subscription for $50/mo?",
                    "What is our projected cash runway?",
                ],
                actions=[
                    ChatAction(label="Savings Opportunities", path="/recommendations", description="Execute cost optimizations"),
                    ChatAction(label="Savings Discovery", path="/savings-discovery", description="Benchmark vendor alternatives"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 7: SPEND OVERVIEW / VENDOR LOOKUP
        # ---------------------------------------------------------------------
        if intent == "SPEND_OVERVIEW":
            # Check if specific vendor is mentioned
            active_subs = [s for s in subscriptions if (s.status or "").lower() == "active"]
            vendor_match = None
            msg_lower = message.lower()
            for s in subscriptions:
                if s.vendor_name and s.vendor_name.lower() in msg_lower:
                    vendor_match = s
                    break

            if vendor_match:
                v_amt = float(getattr(vendor_match, 'latest_amount', None) or getattr(vendor_match, 'average_amount', None) or 0.0)
                amount_str = f"${v_amt:,.2f}" if v_amt > 0 else "Variable"
                cadence = vendor_match.cadence or "monthly"
                next_date = vendor_match.next_billing_date.strftime("%Y-%m-%d") if vendor_match.next_billing_date else "Unscheduled"
                v_card = EvidenceCard(
                    title=f"Vendor: {vendor_match.vendor_name}",
                    data_type="contractual",
                    amount=v_amt,
                    currency="USD",
                    details={
                        "category": vendor_match.category or "General Software",
                        "cadence": cadence,
                        "next_billing_date": next_date,
                        "status": vendor_match.status,
                    },
                    navigation_link="/subscriptions",
                    badge_label=f"{amount_str} / {cadence}",
                    badge_status="neutral",
                )
                v_md = (
                    f"### Subscription Details: **{vendor_match.vendor_name}**\n\n"
                    f"- **Status:** `{vendor_match.status.title() if vendor_match.status else 'Active'}`\n"
                    f"- **Category:** {vendor_match.category or 'Software'}\n"
                    f"- **Billing Cadence:** {cadence.title()}\n"
                    f"- **Billing Amount:** {amount_str}\n"
                    f"- **Next Scheduled Renewal:** {next_date}\n\n"
                    f"Manage subscription details and alert rules on the [Subscriptions Page](/subscriptions)."
                )
                return AssistantQueryResponse(
                    response_text=v_md,
                    is_ai_generated=False,
                    generation_model="SubWise Deterministic Subscription Ledger",
                    intent=intent,
                    data_sufficiency_status=data_status,
                    evidence_cards=[v_card],
                    suggested_followups=[
                        f"Can I afford to upgrade {vendor_match.vendor_name} for an extra $30/mo?",
                        "What are my total subscription expenses?",
                        "What is our cash runway?",
                    ],
                    actions=[
                        ChatAction(label="Manage Subscriptions", path="/subscriptions", description="View and edit subscription plans"),
                        ChatAction(label="Compare Alternatives", path="/savings-discovery", description="Search cheaper vendor options"),
                    ],
                    reporting_period=overview.monthly_briefing.reporting_period,
                    disclaimer=disclaimer,
                )

            # Portfolio spend overview
            card = EvidenceCard(
                title="Monthly Subscription Spend",
                data_type="contractual",
                amount=forward_commit.confirmed_monthly_subscription_commitments,
                currency="USD",
                details={
                    "active_subscriptions_count": len(active_subs),
                    "potential_monthly_commitments": forward_commit.potential_monthly_subscription_commitments,
                    "annual_run_rate": forward_commit.confirmed_annual_subscription_commitments,
                },
                navigation_link="/subscriptions",
                badge_label=f"${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo",
                badge_status="neutral",
            )

            if not active_subs:
                s_md = (
                    f"### Subscription Spend Overview\n\n"
                    f"**Active Recurring Subscriptions:** 0\n"
                    f"**Total Monthly Subscription Commitments:** $0.00/mo\n\n"
                    f"No active recurring software subscriptions were detected in your connected PayPal ledger. "
                    f"When regular vendor transactions occur, SubWise will automatically detect and categorize them."
                )
            else:
                s_md = (
                    f"### Subscription Spend Overview for **{company_name}**\n\n"
                    f"- **Confirmed Monthly Commitments:** **${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo** "
                    f"(${forward_commit.confirmed_annual_subscription_commitments:,.2f}/year)\n"
                    f"- **Active Subscriptions:** {len(active_subs)}\n"
                )
                if forward_commit.potential_monthly_subscription_commitments > 0:
                    s_md += f"- **Potential Trials / Unconfirmed:** ${forward_commit.potential_monthly_subscription_commitments:,.2f}/mo\n"

                s_md += "\n**Active Recurring Vendors:**\n\n| Vendor | Amount | Cadence | Category |\n| :--- | :--- | :--- | :--- |\n"
                for s in active_subs[:6]:
                    amt = float(getattr(s, 'latest_amount', None) or getattr(s, 'average_amount', None) or 0.0)
                    s_md += f"| **{s.vendor_name}** | ${amt:,.2f} | {s.cadence or 'monthly'} | {s.category or 'Software'} |\n"

            return AssistantQueryResponse(
                response_text=s_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Subscription Ledger",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What are our upcoming renewals over the next 30 days?",
                    "Can we afford a new tool for $50/mo?",
                    "What is our cash runway?",
                ],
                actions=[
                    ChatAction(label="Subscriptions Page", path="/subscriptions", description="View active recurring services"),
                    ChatAction(label="Savings Discovery", path="/savings-discovery", description="Benchmark vendor alternatives"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 8: REVENUE INQUIRY
        # ---------------------------------------------------------------------
        if intent == "REVENUE_INQUIRY":
            card = EvidenceCard(
                title="Monthly Operating Revenue",
                data_type="actual",
                amount=hist_actuals.historical_monthly_operating_revenue,
                currency="USD",
                details={
                    "operating_months_analyzed": hist_actuals.operating_months_analyzed,
                    "reporting_period": f"{hist_actuals.reporting_period_start} to {hist_actuals.reporting_period_end}",
                    "non_sub_expenses": hist_actuals.historical_monthly_non_sub_expenses,
                    "net_cash_flow": hist_actuals.historical_monthly_net_cash_flow,
                },
                navigation_link="/reports",
                badge_label=f"${hist_actuals.historical_monthly_operating_revenue:,.2f}/mo",
                badge_status="success" if hist_actuals.historical_monthly_operating_revenue > 0 else "neutral",
            )

            if data_status == "insufficient_data":
                rev_md = (
                    f"### Operating Revenue Analysis\n\n"
                    f"**Verified Operating Revenue:** $0.00/mo\n\n"
                    f"No completed customer sales transactions were identified in your connected PayPal ledger. "
                    f"Under SubWise accounting rules, non-operating wallet top-ups or transfers are strictly excluded from operating revenue."
                )
            else:
                rev_md = (
                    f"### Operating Revenue Analysis for **{company_name}**\n\n"
                    f"- **Monthly Operating Revenue Average:** **${hist_actuals.historical_monthly_operating_revenue:,.2f}/mo**\n"
                    f"- **Operating Months Analyzed:** {hist_actuals.operating_months_analyzed} month(s)\n"
                    f"- **Non-Subscription Operating Expenses:** ${hist_actuals.historical_monthly_non_sub_expenses:,.2f}/mo\n"
                    f"- **Confirmed Subscriptions:** ${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo\n"
                    f"- **Monthly Net Operating Surplus/Deficit:** **${hist_actuals.historical_monthly_net_cash_flow:,.2f}/mo**\n\n"
                    f"View monthly revenue breakdowns on the [Reports Page](/reports)."
                )

            return AssistantQueryResponse(
                response_text=rev_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Accounting Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What are our total subscription costs?",
                    "What is our projected cash runway?",
                    "Summarize our monthly financial report",
                ],
                actions=[
                    ChatAction(label="Revenue Breakdown", path="/reports", description="View historical monthly revenue"),
                    ChatAction(label="Cash Flow Forecast", path="/forecast", description="Project future cash runway"),
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 9: GENERAL_FINTECH (AI Augmentation with Deterministic Fallback)
        # ---------------------------------------------------------------------
        # Prepare verified facts string for LLM or deterministic synthesis
        account_type = (business.account_type or "business").lower()
        facts_summary = (
            f"Account: {company_name} ({account_type.title()})\n"
            f"Data Sufficiency Status: {data_status}\n"
            f"Operating Revenue / Income: ${hist_actuals.historical_monthly_operating_revenue:,.2f}/mo\n"
            f"Non-Subscription Outflows: ${hist_actuals.historical_monthly_non_sub_expenses:,.2f}/mo\n"
            f"Confirmed Subscription Commitments: ${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo\n"
            f"Available Cash / Reserves: ${hist_actuals.verified_available_cash or 0.0:,.2f} ({hist_actuals.cash_provenance})\n"
            f"Cash Runway: {projected.estimated_runway_months or 'Indeterminate'} months\n"
            f"Financial Health Score: {health.score if health.score is not None else 'Withheld (Insufficient data)'}\n"
            f"Reporting Period: {overview.monthly_briefing.reporting_period}\n"
        )

        is_llm = cls.is_llm_configured()
        if is_llm:
            api_key = (settings.GEMINI_API_KEY or settings.LLM_API_KEY or "").strip()
            try:
                system_prompt = (
                    f"You are SubWise AI, an expert, prudent financial advisor for {account_type.capitalize()} accounts. "
                    "You answer questions about spending, savings, subscriptions, and financial health. "
                    "CRITICAL RULES:\n"
                    "1. Base your answer EXCLUSIVELY on the provided VERIFIED FINANCIAL FACTS below.\n"
                    "2. DO NOT invent new vendors, transactions, amounts, or savings.\n"
                    "3. If information is not in the facts, state clearly that it is unavailable in connected records.\n"
                    "4. Distinguish between actual historical data and projected forward estimates.\n"
                    "5. Keep your tone concise, professional, and actionable. Format in clean Markdown without code fences for regular text.\n"
                    "6. Strictly maintain read-only boundaries: never claim to execute payments or modify ledger balances directly."
                )

                history_context = ""
                if history:
                    history_context = "\n\nRECENT CONVERSATION TURNS:\n"
                    for h in history[-4:]:
                        r = h.get("role", "user").capitalize()
                        c = h.get("content", "")
                        history_context += f"{r}: {c}\n"

                full_prompt = (
                    f"{system_prompt}\n\n"
                    f"VERIFIED FINANCIAL FACTS:\n{facts_summary}"
                    f"{history_context}\n\n"
                    f"USER QUESTION: {message}\n\n"
                    f"Provide an evidence-based answer formatted in clean Markdown:"
                )

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            ai_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
                            if ai_text:
                                return AssistantQueryResponse(
                                    response_text=ai_text,
                                    is_ai_generated=True,
                                    generation_model="Google Gemini 1.5 Flash (Verified Financial Baseline)",
                                    intent=intent,
                                    data_sufficiency_status=data_status,
                                    evidence_cards=[],
                                    suggested_followups=[
                                        "What are my upcoming subscription renewals?",
                                        "What is our projected cash runway?",
                                        "Can we afford a new tool for $50/mo?",
                                    ],
                                    actions=[
                                        ChatAction(label="Cash Flow Forecast", path="/forecast", description="Project future runway"),
                                        ChatAction(label="Financial Reports", path="/reports", description="Review detailed financials"),
                                    ],
                                    reporting_period=overview.monthly_briefing.reporting_period,
                                    disclaimer=disclaimer,
                                    llm_provider_configured=True,
                                )
            except Exception:
                pass  # Gracefully fall back to deterministic answer

        # Deterministic General Fallback
        det_md = (
            f"### Financial Overview for **{company_name}**\n\n"
            f"Here is your current verified financial position:\n\n"
            f"- **Data Status:** `{data_status.replace('_', ' ').title()}`\n"
            f"- **Verified Operating Revenue / Income:** ${hist_actuals.historical_monthly_operating_revenue:,.2f}/mo\n"
            f"- **Non-Subscription Outflows:** ${hist_actuals.historical_monthly_non_sub_expenses:,.2f}/mo\n"
            f"- **Confirmed Subscriptions:** ${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo\n"
            f"- **Available Liquid Reserves:** ${hist_actuals.verified_available_cash or 0.0:,.2f}\n"
            f"- **Cash Runway:** {projected.estimated_runway_months or 'Indeterminate'} months\n\n"
            f"You can ask me about:\n"
            f"- **Upcoming Renewals:** *'What payments are due in the next 30 days?'*\n"
            f"- **Affordability:** *'Can I afford a new service for $25/month?'*\n"
            f"- **Reports:** *'Summarize our monthly financial report'* \n"
            f"- **Cash Runway:** *'How long will our cash last?'*"
        )

        return AssistantQueryResponse(
            response_text=det_md,
            is_ai_generated=False,
            generation_model="SubWise Deterministic Intelligence Engine",
            intent=intent,
            data_sufficiency_status=data_status,
            evidence_cards=[],
            suggested_followups=[
                "What are my upcoming renewals?",
                "Can I afford a new subscription for $50/mo?",
                "Summarize our monthly report",
            ],
            actions=[
                ChatAction(label="Forecast Simulator", path="/forecast", description="Simulate scenario projections"),
                ChatAction(label="Financial Reports", path="/reports", description="View executive summaries"),
            ],
            reporting_period=overview.monthly_briefing.reporting_period,
            disclaimer=disclaimer,
            llm_provider_configured=is_llm,
        )
