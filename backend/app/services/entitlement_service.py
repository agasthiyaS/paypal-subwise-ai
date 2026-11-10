from typing import Dict, Any, Optional
from app.models.user import User
from app.models.business import BusinessProfile

class EntitlementTier:
    FREE = "free"
    PRO_INDIVIDUAL = "pro_individual"
    HOUSEHOLD_SHARED = "household_shared"
    BUSINESS_ENTERPRISE = "business_enterprise"


class EntitlementService:
    """
    SubWise AI Monetization & Feature Entitlements Engine:
    Defines tier limits, feature gating, and usage checks without locking out
    existing users or disrupting core workflows.
    """

    TIER_LIMITS = {
        EntitlementTier.FREE: {
            "max_household_members": 1,
            "can_connect_paypal": True,
            "max_scenario_simulations": 3,
            "pdf_export_allowed": True,
            "csv_export_allowed": True,
            "advanced_vendor_comparisons": False,
            "ai_assistant_daily_limit": 25,
            "multi_currency_reconciliation": False,
        },
        EntitlementTier.PRO_INDIVIDUAL: {
            "max_household_members": 2,
            "can_connect_paypal": True,
            "max_scenario_simulations": 20,
            "pdf_export_allowed": True,
            "csv_export_allowed": True,
            "advanced_vendor_comparisons": True,
            "ai_assistant_daily_limit": 100,
            "multi_currency_reconciliation": True,
        },
        EntitlementTier.HOUSEHOLD_SHARED: {
            "max_household_members": 10,
            "can_connect_paypal": True,
            "max_scenario_simulations": 50,
            "pdf_export_allowed": True,
            "csv_export_allowed": True,
            "advanced_vendor_comparisons": True,
            "ai_assistant_daily_limit": 250,
            "multi_currency_reconciliation": True,
        },
        EntitlementTier.BUSINESS_ENTERPRISE: {
            "max_household_members": 100,
            "can_connect_paypal": True,
            "max_scenario_simulations": 9999,
            "pdf_export_allowed": True,
            "csv_export_allowed": True,
            "advanced_vendor_comparisons": True,
            "ai_assistant_daily_limit": 9999,
            "multi_currency_reconciliation": True,
        },
    }

    @classmethod
    def resolve_tier(cls, user: Optional[User], business: Optional[BusinessProfile]) -> str:
        if not user:
            return EntitlementTier.FREE

        if getattr(user, "is_admin", False):
            return EntitlementTier.BUSINESS_ENTERPRISE

        acct_type = (business.account_type if business else "individual") or "individual"
        if acct_type == "business":
            return EntitlementTier.BUSINESS_ENTERPRISE
        elif acct_type == "household":
            return EntitlementTier.HOUSEHOLD_SHARED
        else:
            return EntitlementTier.PRO_INDIVIDUAL

    @classmethod
    def get_entitlements(cls, user: Optional[User], business: Optional[BusinessProfile]) -> Dict[str, Any]:
        tier = cls.resolve_tier(user, business)
        limits = cls.TIER_LIMITS.get(tier, cls.TIER_LIMITS[EntitlementTier.FREE])
        return {
            "tier": tier,
            "account_type": business.account_type if business else "individual",
            "is_admin": bool(user and getattr(user, "is_admin", False)),
            "features": limits,
        }

    @classmethod
    def check_feature_access(
        cls,
        feature_name: str,
        user: Optional[User],
        business: Optional[BusinessProfile]
    ) -> bool:
        entitlements = cls.get_entitlements(user, business)
        feature_val = entitlements["features"].get(feature_name)
        if isinstance(feature_val, bool):
            return feature_val
        if isinstance(feature_val, (int, float)):
            return feature_val > 0
        return True

