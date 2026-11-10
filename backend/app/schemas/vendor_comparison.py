from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class AlternativeOption(BaseModel):
    name: str
    tier: str
    price: float
    billing_frequency: str # 'monthly' or 'annual'
    monthly_equivalent: float
    features: List[str] = []
    trade_offs: List[str] = []
    estimated_monthly_savings: float
    estimated_annual_savings: float
    source: str
    source_date: str

class VendorComparisonItem(BaseModel):
    id: str
    category: str # 'Streaming', 'Cloud Storage', 'Productivity', 'Telecom', 'Groceries'
    current_service_name: str
    current_tier: str
    current_price: float
    current_frequency: str
    current_monthly_cost: float
    recommended_alternative: AlternativeOption
    other_options: List[AlternativeOption] = []
    confidence: str # 'High', 'Medium', 'Low'
    urgency: str # 'Immediate', 'Review at Renewal', 'Discretionary'
    summary_verdict: str

class VendorCatalogCategory(BaseModel):
    category: str
    description: str
    items: List[VendorComparisonItem] = []

class SavingsDiscoverySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_identified_monthly_savings: float
    total_identified_annual_savings: float
    ranked_opportunities: List[VendorComparisonItem] = []
    top_actions: List[str] = []
    disclaimer: str

