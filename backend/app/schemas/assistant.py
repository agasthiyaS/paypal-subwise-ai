from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any


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


class AssistantQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    response_text: str
    is_ai_generated: bool
    generation_model: str
    intent: str
    data_sufficiency_status: str  # 'sufficient_data', 'limited_data', 'insufficient_data'
    evidence_cards: List[EvidenceCard] = []
    suggested_followups: List[str] = []
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

