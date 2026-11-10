import re
from typing import Tuple, Dict, Any

# Canonical Merchant Knowledge Base for FinTech & SaaS
MERCHANT_REGISTRY = {
    "aws": {
        "canonical": "AWS",
        "category": "Cloud Infrastructure",
        "redundancy_group": "cloud_hosting",
        "default_tier": 1,
        "is_essential": True
    },
    "amazon web services": {
        "canonical": "AWS",
        "category": "Cloud Infrastructure",
        "redundancy_group": "cloud_hosting",
        "default_tier": 1,
        "is_essential": True
    },
    "google *workspace": {
        "canonical": "Google Workspace",
        "category": "Productivity & Email",
        "redundancy_group": "office_suite",
        "default_tier": 1,
        "is_essential": True
    },
    "gsuite": {
        "canonical": "Google Workspace",
        "category": "Productivity & Email",
        "redundancy_group": "office_suite",
        "default_tier": 1,
        "is_essential": True
    },
    "google cloud": {
        "canonical": "Google Cloud",
        "category": "Cloud Infrastructure",
        "redundancy_group": "cloud_hosting",
        "default_tier": 1,
        "is_essential": True
    },
    "slack": {
        "canonical": "Slack",
        "category": "Team Collaboration",
        "redundancy_group": "messaging_collab",
        "default_tier": 2,
        "is_essential": True
    },
    "microsoft *365": {
        "canonical": "Microsoft 365",
        "category": "Productivity & Email",
        "redundancy_group": "office_suite",
        "default_tier": 2,
        "is_essential": True
    },
    "msft *teams": {
        "canonical": "Microsoft Teams",
        "category": "Team Collaboration",
        "redundancy_group": "messaging_collab",
        "default_tier": 2,
        "is_essential": True
    },
    "github": {
        "canonical": "GitHub",
        "category": "Developer Tools",
        "redundancy_group": "version_control",
        "default_tier": 1,
        "is_essential": True
    },
    "gitlab": {
        "canonical": "GitLab",
        "category": "Developer Tools",
        "redundancy_group": "version_control",
        "default_tier": 1,
        "is_essential": True
    },
    "openai": {
        "canonical": "OpenAI",
        "category": "AI & Machine Learning",
        "redundancy_group": "ai_api",
        "default_tier": 2,
        "is_essential": True
    },
    "chatgpt": {
        "canonical": "OpenAI ChatGPT",
        "category": "AI & Machine Learning",
        "redundancy_group": "ai_assistant",
        "default_tier": 3,
        "is_essential": False
    },
    "anthropic": {
        "canonical": "Anthropic Claude",
        "category": "AI & Machine Learning",
        "redundancy_group": "ai_assistant",
        "default_tier": 3,
        "is_essential": False
    },
    "hubspot": {
        "canonical": "HubSpot",
        "category": "CRM & Marketing",
        "redundancy_group": "crm_sales",
        "default_tier": 2,
        "is_essential": True
    },
    "cloudsoft": {
        "canonical": "CloudSoft",
        "category": "Cloud & IT Management",
        "redundancy_group": "cloud_hosting",
        "default_tier": 2,
        "is_essential": True
    },
    "salesforce": {
        "canonical": "Salesforce",
        "category": "CRM & Marketing",
        "redundancy_group": "crm_sales",
        "default_tier": 1,
        "is_essential": True
    },
    "zoom": {
        "canonical": "Zoom",
        "category": "Video Conferencing",
        "redundancy_group": "video_conferencing",
        "default_tier": 3,
        "is_essential": False
    },
    "notion": {
        "canonical": "Notion",
        "category": "Knowledge & Docs",
        "redundancy_group": "docs_wiki",
        "default_tier": 2,
        "is_essential": True
    },
    "figma": {
        "canonical": "Figma",
        "category": "Design & Prototyping",
        "redundancy_group": "design_suite",
        "default_tier": 2,
        "is_essential": True
    },
    "canva": {
        "canonical": "Canva",
        "category": "Design & Marketing Graphics",
        "redundancy_group": "design_suite",
        "default_tier": 3,
        "is_essential": False
    },
    "datadog": {
        "canonical": "Datadog",
        "category": "DevOps & Monitoring",
        "redundancy_group": "observability",
        "default_tier": 2,
        "is_essential": True
    },
    "new relic": {
        "canonical": "New Relic",
        "category": "DevOps & Monitoring",
        "redundancy_group": "observability",
        "default_tier": 2,
        "is_essential": True
    },
    "vercel": {
        "canonical": "Vercel",
        "category": "Cloud Infrastructure",
        "redundancy_group": "frontend_hosting",
        "default_tier": 2,
        "is_essential": True
    },
    "quickbooks": {
        "canonical": "QuickBooks Online",
        "category": "Accounting & Finance",
        "redundancy_group": "accounting",
        "default_tier": 1,
        "is_essential": True
    },
    "xero": {
        "canonical": "Xero",
        "category": "Accounting & Finance",
        "redundancy_group": "accounting",
        "default_tier": 1,
        "is_essential": True
    },
    "jira": {
        "canonical": "Atlassian Jira",
        "category": "Project Management",
        "redundancy_group": "project_management",
        "default_tier": 2,
        "is_essential": True
    },
    "asana": {
        "canonical": "Asana",
        "category": "Project Management",
        "redundancy_group": "project_management",
        "default_tier": 3,
        "is_essential": False
    },
    "linear": {
        "canonical": "Linear",
        "category": "Project Management",
        "redundancy_group": "project_management",
        "default_tier": 2,
        "is_essential": True
    },
    "trello": {
        "canonical": "Trello",
        "category": "Project Management",
        "redundancy_group": "project_management",
        "default_tier": 3,
        "is_essential": False
    },
    "dropbox": {
        "canonical": "Dropbox Business",
        "category": "Cloud Storage",
        "redundancy_group": "cloud_storage",
        "default_tier": 3,
        "is_essential": False
    },
    "box.com": {
        "canonical": "Box",
        "category": "Cloud Storage",
        "redundancy_group": "cloud_storage",
        "default_tier": 3,
        "is_essential": False
    },
    "mailchimp": {
        "canonical": "Mailchimp",
        "category": "Email Marketing",
        "redundancy_group": "email_marketing",
        "default_tier": 3,
        "is_essential": False
    },
    "loom": {
        "canonical": "Loom",
        "category": "Video Messaging",
        "redundancy_group": "video_messaging",
        "default_tier": 3,
        "is_essential": False
    },
    "adobe": {
        "canonical": "Adobe Creative Cloud",
        "category": "Design & Media",
        "redundancy_group": "design_suite",
        "default_tier": 2,
        "is_essential": True,
        "is_known_saas": True,
        "variable_billing": False
    },
    "adobe *creative": {
        "canonical": "Adobe Creative Cloud",
        "category": "Design & Media",
        "redundancy_group": "design_suite",
        "default_tier": 2,
        "is_essential": True,
        "is_known_saas": True,
        "variable_billing": False
    },
    "adobe systems": {
        "canonical": "Adobe Creative Cloud",
        "category": "Design & Media",
        "redundancy_group": "design_suite",
        "default_tier": 2,
        "is_essential": True,
        "is_known_saas": True,
        "variable_billing": False
    },
    "twilio": {
        "canonical": "Twilio",
        "category": "Communications API & SMS",
        "redundancy_group": "comm_api",
        "default_tier": 2,
        "is_essential": True,
        "is_known_saas": True,
        "variable_billing": True
    },
    "1password": {
        "canonical": "1Password",
        "category": "Security & Identity",
        "redundancy_group": "password_mgmt",
        "default_tier": 1,
        "is_essential": True
    }
}

class TransactionNormalizer:
    @staticmethod
    def normalize_vendor_and_category(raw_descriptor: str) -> Dict[str, Any]:
        """
        Normalizes noisy transaction descriptions into canonical merchant profiles.
        E.g.: 'AMZN *AWS CLOUD 102948-US' -> canonical: 'AWS', category: 'Cloud Infrastructure'
        """
        cleaned = raw_descriptor.strip().lower()
        # Remove noisy prefix/suffix characters
        cleaned = re.sub(r'[\*\#\/\:\_\-\d]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Check non-operating balance adjustments, account funding, and capital transfers
        FUNDING_KEYWORDS = [
            "initial balance", "account funding", "balance adjustment", "general funding",
            "deposit", "bank transfer", "wallet funding", "reserve deposit", "top up",
            "reversal adjustment", "fee reversal", "paypal balance"
        ]
        if any(kw in cleaned or kw in raw_descriptor.lower() for kw in FUNDING_KEYWORDS):
            return {
                "normalized_vendor": "PayPal Balance Adjustment",
                "category": "Account Funding / Balance Adjustment",
                "redundancy_group": None,
                "priority_tier": 1,
                "is_essential": True,
                "is_funding": True,
                "is_known_saas": False,
                "is_currency_conversion": False
            }

        # Check internal PayPal transfer / currency conversion / settlement descriptors
        PAYPAL_TRANSFER_KEYWORDS = [
            "paypal transaction", "currency conversion", "exchange rate", "conversion leg",
            "internal transfer", "transfer to paypal", "transfer from paypal"
        ]
        if any(kw in cleaned or kw in raw_descriptor.lower() for kw in PAYPAL_TRANSFER_KEYWORDS):
            return {
                "normalized_vendor": "PayPal Transfer",
                "category": "Payment Transfer / Currency Conversion",
                "redundancy_group": None,
                "priority_tier": 3,
                "is_essential": False,
                "is_known_saas": False,
                "variable_billing": False,
                "is_funding": False,
                "is_currency_conversion": True
            }

        # Check dictionary matches directly against cleaned descriptor
        for pattern, meta in MERCHANT_REGISTRY.items():
            regex = re.escape(pattern).replace(r'\*', '.*')
            if re.search(regex, cleaned, re.IGNORECASE) or re.search(regex, raw_descriptor, re.IGNORECASE):
                var_billing = meta.get("variable_billing", False)
                if not var_billing and meta["canonical"] in ["AWS", "Google Cloud", "OpenAI", "Twilio", "Datadog", "New Relic", "Vercel"]:
                    var_billing = True

                return {
                    "normalized_vendor": meta["canonical"],
                    "category": meta["category"],
                    "redundancy_group": meta.get("redundancy_group"),
                    "priority_tier": meta.get("default_tier", 2),
                    "is_essential": meta.get("is_essential", True),
                    "is_known_saas": True,
                    "variable_billing": var_billing,
                    "is_funding": False,
                    "is_currency_conversion": False
                }

        # Advanced vendor candidate extraction:
        # Handles descriptors like 'Monthly Software Subscription - CloudSoft',
        # 'Payment to CloudSoft', 'CloudSoft - Monthly Subscription'
        NOISE_WORDS = {
            "monthly", "annual", "yearly", "quarterly", "weekly", "biweekly",
            "software", "subscription", "subscriptions", "recurring", "service", "services",
            "payment", "payments", "charge", "charges", "bill", "billing", "invoice",
            "order", "orders", "purchase", "purchases", "to", "for", "from", "via", "fee", "plan"
        }

        vendor_candidate = None
        # Check separated segments: e.g. "Monthly Software Subscription - CloudSoft"
        parts = re.split(r'[\-\:\|]', raw_descriptor)
        if len(parts) >= 2:
            p0_words = [w for w in re.findall(r'[a-zA-Z0-9]+', parts[0]) if w.lower() not in NOISE_WORDS]
            p1_words = [w for w in re.findall(r'[a-zA-Z0-9]+', parts[1]) if w.lower() not in NOISE_WORDS]
            if not p0_words and p1_words:
                vendor_candidate = " ".join(p1_words)
            elif p0_words:
                vendor_candidate = " ".join(p0_words)

        if not vendor_candidate:
            words = [w for w in re.findall(r'[a-zA-Z0-9]+', raw_descriptor) if w.lower() not in NOISE_WORDS]
            if words:
                vendor_candidate = " ".join(words[:2])

        if vendor_candidate:
            # Check candidate against registry
            cand_clean = vendor_candidate.lower()
            for pattern, meta in MERCHANT_REGISTRY.items():
                if pattern in cand_clean or cand_clean in pattern:
                    return {
                        "normalized_vendor": meta["canonical"],
                        "category": meta["category"],
                        "redundancy_group": meta.get("redundancy_group"),
                        "priority_tier": meta.get("default_tier", 2),
                        "is_essential": meta.get("is_essential", True),
                        "is_known_saas": True,
                        "variable_billing": meta.get("variable_billing", False),
                        "is_funding": False,
                        "is_currency_conversion": False
                    }

        # Fallback heuristic: clean descriptor
        if not vendor_candidate:
            words = raw_descriptor.replace("*", " ").replace("-", " ").split()
            vendor_candidate = words[0].capitalize() if words else "Vendor"

        return {
            "normalized_vendor": vendor_candidate,
            "category": "General Operations",
            "redundancy_group": None,
            "priority_tier": 3,
            "is_essential": False,
            "is_known_saas": False,
            "variable_billing": False,
            "is_funding": False,
            "is_currency_conversion": False
        }

