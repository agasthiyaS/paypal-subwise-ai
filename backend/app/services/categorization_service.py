import re
from typing import Dict, Any, Optional, Tuple

EXPENSE_CATEGORIES = [
    "Food & Groceries",
    "Shopping",
    "Transportation",
    "Electricity & Utilities",
    "Housing & Rent",
    "Healthcare",
    "Education",
    "Entertainment",
    "Subscriptions",
    "Other"
]

# High-precision keyword and pattern rules
CATEGORY_RULES = {
    "Food & Groceries": [
        r"\b(trader joe|walmart|kroger|whole foods|safeway|costco|aldi|target|supermarket|grocery|groceries|market|publix|heb|meijer|food lion|wegmans|instacart|sprouts)\b",
        r"\b(bakery|butcher|deli|farmers market|convenience store|7-eleven|wawa)\b",
        r"\b(restaurant|cafe|coffee|starbucks|dunkin|chipotle|mcdonald|subway|domino|pizza|burger|door dash|doordash|uber eats|ubereats|grubhub)\b"
    ],
    "Electricity & Utilities": [
        r"\b(electric|power|energy|water|gas|utility|utilities|sewer|trash|waste management)\b",
        r"\b(broadband|internet|fiber|wifi|telecom|at&t|verizon|t-mobile|comcast|xfinity|spectrum|charter|centurylink)\b",
        r"\b(pg&e|coned|con edison|duke energy|southern company|national grid|fpl)\b"
    ],
    "Subscriptions": [
        r"\b(netflix|spotify|hulu|disney\+|disneyplus|apple music|youtube premium|amazon prime|prime video|hbo|max\.com|paramount|peacock)\b",
        r"\b(cloudsoft|adobe|microsoft 365|office 365|github|gitlab|notion|slack|zoom|dropbox|google storage|google one|aws|digitalocean|heroku|openai|chatgpt)\b"
    ],
    "Transportation": [
        r"\b(uber|lyft|taxi|cab|rideshare)\b",
        r"\b(gasoline|gas station|fuel|petrol|shell|chevron|exxon|mobil|bp|texaco|speedway|marathon)\b",
        r"\b(transit|metro|subway|bus|train|amtrak|mta|bart|caltrain)\b",
        r"\b(parking|toll|ezpass|fasstrak|auto repair|jiffy lube|oil change|tire)\b",
        r"\b(airline|delta|united airlines|american airlines|southwest|airfare|flight)\b"
    ],
    "Housing & Rent": [
        r"\b(rent|rental|mortgage|hoa|homeowners association|property management|landlord|apartment|lease|storage unit)\b"
    ],
    "Healthcare": [
        r"\b(pharmacy|prescription|rx|cvs|walgreens|rite aid)\b",
        r"\b(doctor|physician|dental|dentist|orthodontist|optometry|vision|clinic|hospital|urgent care|medical|health care|labcorp|quest diagnostics)\b"
    ],
    "Education": [
        r"\b(tuition|school|university|college|academy|student loan|textbook|coursera|udemy|edx|skillshare|duolingo|chegg)\b"
    ],
    "Entertainment": [
        r"\b(cinema|movie|theatre|amc|regal|ticketmaster|eventbrite|stubhub|concert|festival)\b",
        r"\b(steam|playstation|playstation network|psn|xbox|nintendo|epic games|ea games|blizzard|twitch)\b",
        r"\b(amusement park|museum|zoo|aquarium|bowling|golf)\b"
    ],
    "Shopping": [
        r"\b(amazon|ebay|best buy|walmart\.com|target\.com|etsy|shopify)\b",
        r"\b(ikea|home depot|lowe'?s|wayfair|bed bath)\b",
        r"\b(clothing|apparel|shoes|nike|adidas|zara|h&m|nordstrom|macy'?s|tj maxx|marshalls)\b",
        r"\b(electronics|apple store|hardware store)\b"
    ]
}

class CategorizationService:
    @staticmethod
    def categorize(description: str, merchant: Optional[str] = None) -> Tuple[str, str, float]:
        """
        Classifies an expense into a standardized category.
        Returns: (category, match_reason, confidence)
        """
        text = f"{merchant or ''} {description or ''}".lower()
        if not text.strip():
            return "Other", "empty_description", 0.0

        # Exact merchant matching first
        for cat, patterns in CATEGORY_RULES.items():
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    matched_term = match.group(0)
                    return cat, f"matched_rule: '{matched_term}'", 0.95

        return "Other", "unclassified_fallback", 0.30

    @staticmethod
    def get_standard_categories():
        return EXPENSE_CATEGORIES

