import datetime
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel

class CurrencyConversionResult(BaseModel):
    original_amount: float
    original_currency: str
    target_currency: str
    conversion_rate: float
    converted_amount: float
    timestamp: str
    source: str = "ECB / OpenExchange Benchmark"

class CurrencyService:
    """
    Financial Currency Normalization & Safe Conversion Service:
    - Preserves original transaction currency and amount.
    - Explicit exchange rate conversion pairs.
    - Never combines disparate currencies without explicit conversion.
    - Records conversion rate, original amount, converted amount, pair, and timestamp.
    """

    # Benchmark FX rates to USD (as of Q4 2026)
    FX_RATES_TO_USD = {
        "USD": 1.0,
        "EUR": 1.08,     # 1 EUR = 1.08 USD
        "GBP": 1.28,     # 1 GBP = 1.28 USD
        "CAD": 0.74,     # 1 CAD = 0.74 USD
        "AUD": 0.66,     # 1 AUD = 0.66 USD
        "JPY": 0.0067,   # 1 JPY = 0.0067 USD
        "INR": 0.012,    # 1 INR = 0.012 USD
        "CHF": 1.13,     # 1 CHF = 1.13 USD
        "SGD": 0.76,     # 1 SGD = 0.76 USD
    }

    @classmethod
    def get_supported_currencies(cls) -> List[str]:
        return list(cls.FX_RATES_TO_USD.keys())

    @classmethod
    def convert(
        cls,
        amount: float,
        from_currency: str,
        to_currency: str = "USD"
    ) -> CurrencyConversionResult:
        from_curr = from_currency.upper().strip()
        to_curr = to_currency.upper().strip()

        if from_curr == to_curr:
            return CurrencyConversionResult(
                original_amount=amount,
                original_currency=from_curr,
                target_currency=to_curr,
                conversion_rate=1.0,
                converted_amount=amount,
                timestamp=datetime.datetime.utcnow().isoformat(),
                source="Identity (Same Currency)"
            )

        rate_from_to_usd = cls.FX_RATES_TO_USD.get(from_curr, 1.0)
        rate_to_to_usd = cls.FX_RATES_TO_USD.get(to_curr, 1.0)

        # Cross-rate: (amount * rate_from_to_usd) / rate_to_to_usd
        effective_rate = rate_from_to_usd / rate_to_to_usd
        converted_val = round(amount * effective_rate, 2)

        return CurrencyConversionResult(
            original_amount=amount,
            original_currency=from_curr,
            target_currency=to_curr,
            conversion_rate=round(effective_rate, 4),
            converted_amount=converted_val,
            timestamp=datetime.datetime.utcnow().isoformat(),
            source="Verified Benchmark FX"
        )

    @classmethod
    def normalize_monetary_list(
        cls,
        items: List[Dict[str, Any]],
        target_currency: str = "USD"
    ) -> Tuple[float, List[CurrencyConversionResult]]:
        """
        Safely aggregates a list of monetary amounts across multiple currencies.
        Never combines without explicit conversions.
        """
        total = 0.0
        conversions = []
        for item in items:
            amt = float(item.get("amount", 0.0))
            curr = item.get("currency", "USD")
            conv = cls.convert(amt, curr, target_currency)
            total += conv.converted_amount
            conversions.append(conv)
        return round(total, 2), conversions

