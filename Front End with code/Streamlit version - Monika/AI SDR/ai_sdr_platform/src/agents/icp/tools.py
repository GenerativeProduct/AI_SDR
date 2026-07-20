from __future__ import annotations

import re
from typing import Iterable

INDUSTRY_SYNONYMS = {
    "saas": "software",
    "software": "software",
    "healthtech": "healthcare_technology",
    "health care": "healthcare",
    "fintech": "financial_technology",
    "ecommerce": "ecommerce",
    "e-commerce": "ecommerce",
    "revops": "revenue_operations",
}

GEO_SYNONYMS = {
    "us": "US",
    "usa": "US",
    "united states": "US",
    "uk": "UK",
    "united kingdom": "UK",
    "europe": "Europe",
    "eu": "Europe",
    "india": "India",
    "apac": "APAC",
}

PERSONA_ALIASES = {
    "revops": [
        "VP Revenue Operations",
        "Director of Revenue Operations",
        "Head of Revenue Operations",
    ],
    "sales ops": [
        "VP Sales Operations",
        "Director of Sales Operations",
        "Head of Sales Operations",
    ],
    "marketing ops": [
        "Director of Marketing Operations",
        "Head of Marketing Operations",
    ],
}

EMPLOYEE_BANDS = {
    "small": (1, 50),
    "smb": (1, 200),
    "mid-market": (200, 1000),
    "mid market": (200, 1000),
    "enterprise": (1000, None),
}

REVENUE_BANDS_MILLION = {
    "seed": (0, 5),
    "growth": (5, 50),
    "mid-market": (10, 200),
    "enterprise": (200, None),
}


def slugify_name(parts: Iterable[str]) -> str:
    text = " ".join([p.strip() for p in parts if p and p.strip()])
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)


def normalize_industry(value: str) -> str:
    cleaned = value.strip().lower()
    return INDUSTRY_SYNONYMS.get(cleaned, cleaned.replace(" ", "_"))


def normalize_geo(value: str) -> str:
    cleaned = value.strip().lower()
    return GEO_SYNONYMS.get(cleaned, value.strip())


def expand_persona_alias(value: str) -> list[str]:
    cleaned = value.strip().lower()
    return PERSONA_ALIASES.get(cleaned, [value.strip()])
