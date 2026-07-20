from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

import requests

from ai_sdr_platform.src.agents.icp.models import ICPDefinition
from ai_sdr_platform.src.agents.prospect_discovery.models import (
    DiscoveredAccount,
    DiscoveredContact,
)


class AccountDiscoveryProvider(Protocol):
    name: str

    def search_accounts(
        self, icp: ICPDefinition, limit: int
    ) -> list[DiscoveredAccount]:
        ...


class ContactDiscoveryProvider(Protocol):
    name: str

    def search_contacts(
        self,
        accounts: list[DiscoveredAccount],
        target_titles: list[str],
        target_seniorities: list[str],
    ) -> list[DiscoveredContact]:
        ...


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.lower().strip().encode()).hexdigest()[:16]
    return f"{prefix}_{digest}"


def search_terms(icp: ICPDefinition) -> list[str]:
    values = [
        *icp.account_criteria.industries,
        *icp.account_criteria.tech_stack_signals,
        *icp.account_criteria.funding_stages,
    ]
    terms: list[str] = []
    for value in values:
        cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", value).strip()
        if cleaned and cleaned.lower() not in {"company", "business"}:
            terms.append(cleaned)
    return list(dict.fromkeys(terms))[:8]


def gleif_country_code(icp: ICPDefinition) -> str | None:
    aliases = {
        "us": "US",
        "usa": "US",
        "united states": "US",
        "uk": "GB",
        "united kingdom": "GB",
        "great britain": "GB",
        "india": "IN",
        "canada": "CA",
        "australia": "AU",
        "germany": "DE",
        "france": "FR",
        "singapore": "SG",
    }
    for value in icp.account_criteria.geographies:
        code = aliases.get(value.lower().strip())
        if code:
            return code
    return None


def opencorporates_jurisdiction_code(icp: ICPDefinition) -> str | None:
    aliases = {
        "washington": "us_wa",
        "washington, united states": "us_wa",
        "washington, us": "us_wa",
        "california": "us_ca",
        "new york": "us_ny",
        "texas": "us_tx",
        "delaware": "us_de",
        "florida": "us_fl",
        "united kingdom": "gb",
        "uk": "gb",
        "great britain": "gb",
    }
    values = [value.lower().strip() for value in icp.account_criteria.geographies]
    for value in values:
        if value in aliases:
            return aliases[value]
    if "united states" in values or "us" in values or "usa" in values:
        return "us"
    return None


def discovery_queries(icp: ICPDefinition) -> list[str]:
    industries = icp.account_criteria.industries or ["software"]
    geographies = icp.account_criteria.geographies or []
    tech = icp.account_criteria.tech_stack_signals or []
    buying = icp.persona_criteria.buying_signals or []
    titles = icp.persona_criteria.titles or []
    queries: list[str] = []
    geo_text = " ".join(geographies[:2])
    for industry in industries[:2]:
        base = " ".join(item for item in [industry, "companies", "headquartered in", geo_text] if item).strip()
        if base:
            queries.append(base)
        if tech:
            queries.append(f"{base} customer story {' '.join(tech[:3])}".strip())
        if titles:
            queries.append(f"{base} leadership team {' '.join(titles[:2])}".strip())
    return list(dict.fromkeys(query for query in queries if query))[:4]


def _clean_company_name(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    text = re.sub(r"\s*[\-|–|—|:]\s*(LinkedIn|Crunchbase|PitchBook|Glassdoor|Indeed|Careers).*$", "", text, flags=re.I)
    text = re.sub(r"\s*\|\s*.*$", "", text)
    text = re.sub(r"\s+-\s+.*$", "", text)
    return text.strip(" .,-")


def _domain_from_url(url: str) -> str:
    return re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/")[0]).lower()


_ACCOUNT_BLOCKED_DOMAINS = {
    "crunchbase.com",
    "techcrunch.com",
    "youtube.com",
    "wikipedia.org",
    "appsrunworld.com",
    "theirstack.com",
    "6sense.com",
    "zoominfo.com",
    "apollo.io",
    "clay.com",
    "rocketreach.co",
    "signalhire.com",
    "adapt.io",
    "contactout.com",
    "growjo.com",
    "builtwith.com",
}

_ACCOUNT_BAD_TITLE_PATTERNS = [
    "companies that use",
    "company overview",
    "contact details",
    "competitors",
    "best ",
    "top ",
    "list of ",
    "raises $",
    "secures $",
    "funding round",
    "faqs",
    "data providers",
    "wikipedia",
    "youtube",
    "news:",
]


def _is_company_account_hit(title: str, url: str, domain: str) -> bool:
    lowered = title.lower()
    clean_domain = domain or _domain_from_url(url)
    if not title or len(title) < 3:
        return False
    if any(blocked in clean_domain for blocked in _ACCOUNT_BLOCKED_DOMAINS):
        return False
    if any(pattern in lowered for pattern in _ACCOUNT_BAD_TITLE_PATTERNS):
        return False
    if "linkedin.com/company/" in url:
        return True
    if any(path in url.lower() for path in ["/company/", "/companies/"]):
        return True
    if clean_domain and not any(
        host in clean_domain
        for host in ["google.", "bing.", "duckduckgo.", "search.", "facebook.com", "x.com"]
    ):
        return True
    return False


def _extract_person_name_title(text: str, target_titles: list[str]) -> tuple[str, str] | None:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if not compact:
        return None
    title_terms = target_titles or [
        "VP Sales",
        "CRO",
        "Head of Sales",
        "Director of Revenue Operations",
        "Revenue Operations",
    ]
    title_pattern = "|".join(re.escape(title) for title in title_terms)
    patterns = [
        rf"(?P<name>[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){{1,3}})\s*[-–—|,]\s*(?P<title>{title_pattern})",
        rf"(?P<title>{title_pattern})\s*[-–—|,]\s*(?P<name>[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){{1,3}})",
    ]
    for pattern in patterns:
        match = re.search(pattern, compact, flags=re.I)
        if match:
            name = match.group("name").strip()
            title = match.group("title").strip()
            if len(name.split()) >= 2:
                return name, title
    return None


def _seen_company(seen: set[str], name: str) -> bool:
    key = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    if not key:
        return True
    if key in seen:
        return True
    seen.add(key)
    return False


@dataclass
class GLEIFAccountProvider:
    base_url: str = "https://api.gleif.org/api/v1"
    timeout_seconds: float = 15.0
    name: str = "gleif"

    def search_accounts(
        self, icp: ICPDefinition, limit: int
    ) -> list[DiscoveredAccount]:
        results: list[DiscoveredAccount] = []
        terms = search_terms(icp)
        if not terms:
            return results
        country_code = gleif_country_code(icp)
        for term in terms:
            params = {
                "filter[entity.legalName]": term,
                "page[size]": min(max(limit * 2, 5), 50),
            }
            if country_code:
                params["filter[entity.legalAddress.country]"] = country_code
            response = requests.get(
                f"{self.base_url.rstrip('/')}/lei-records",
                params=params,
                headers={"accept": "application/vnd.api+json"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            for record in response.json().get("data", []):
                account = self._to_account(record, icp)
                if account:
                    results.append(account)
                if len(results) >= limit:
                    return results
        return results

    def _to_account(
        self, record: dict[str, Any], icp: ICPDefinition
    ) -> DiscoveredAccount | None:
        attributes = record.get("attributes") or {}
        entity = attributes.get("entity") or {}
        legal_name = entity.get("legalName") or {}
        name = str(legal_name.get("name") or "").strip()
        if not name:
            return None
        address = entity.get("legalAddress") or {}
        country = str(address.get("country") or "Unknown")
        legal_form = entity.get("legalForm") or {}
        legal_form_name = str(legal_form.get("other") or legal_form.get("id") or "")
        return DiscoveredAccount(
            account_id=stable_id("gleif", str(record.get("id") or name)),
            icp_id=icp.icp_id,
            company_name=name,
            website=None,
            industry=legal_form_name or "Unknown",
            location=country,
            employee_count=0,
            revenue_range=None,
            source="gleif",
            fit_score=0,
            fit_reasons=["real legal-entity record from GLEIF"],
            status="new",
        )


@dataclass
class CompaniesHouseAccountProvider:
    api_key: str
    base_url: str = "https://api.company-information.service.gov.uk"
    timeout_seconds: float = 15.0
    name: str = "companies_house"

    def search_accounts(
        self, icp: ICPDefinition, limit: int
    ) -> list[DiscoveredAccount]:
        if not self.api_key.strip():
            return []
        results: list[DiscoveredAccount] = []
        seen: set[str] = set()
        for query in discovery_queries(icp):
            response = requests.get(
                f"{self.base_url.rstrip('/')}/search/companies",
                params={"q": query, "items_per_page": min(max(limit * 2, 5), 50)},
                auth=(self.api_key, ""),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            for item in response.json().get("items", []) or []:
                name = str(item.get("title") or "").strip()
                if not name:
                    continue
                if _seen_company(seen, name):
                    continue
                address = item.get("address") or {}
                location = ", ".join(
                    str(value)
                    for value in (
                        address.get("locality"),
                        address.get("region"),
                        address.get("country"),
                    )
                    if value
                ) or "United Kingdom"
                results.append(
                    DiscoveredAccount(
                        account_id=stable_id("companies_house", str(item.get("company_number") or name)),
                        icp_id=icp.icp_id,
                        company_name=name,
                        website=None,
                        industry=str(item.get("company_type") or "UK company"),
                        location=location,
                        employee_count=0,
                        revenue_range=None,
                        source="companies_house",
                        fit_score=0,
                        fit_reasons=["real Companies House company record"],
                        status="new",
                    )
                )
                if len(results) >= limit:
                    return results
        return results


@dataclass
class OpenCorporatesAccountProvider:
    api_token: str = ""
    base_url: str = "https://api.opencorporates.com/v0.4"
    timeout_seconds: float = 15.0
    name: str = "opencorporates"

    def search_accounts(
        self, icp: ICPDefinition, limit: int
    ) -> list[DiscoveredAccount]:
        results: list[DiscoveredAccount] = []
        seen: set[str] = set()
        jurisdiction = opencorporates_jurisdiction_code(icp)
        for query in discovery_queries(icp):
            params: dict[str, Any] = {
                "q": query,
                "per_page": min(max(limit * 2, 5), 30),
            }
            if jurisdiction:
                params["jurisdiction_code"] = jurisdiction
            if self.api_token:
                params["api_token"] = self.api_token
            response = requests.get(
                f"{self.base_url.rstrip('/')}/companies/search",
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            for row in (response.json().get("results") or {}).get("companies", []) or []:
                company = row.get("company") or {}
                name = str(company.get("name") or "").strip()
                if not name:
                    continue
                if _seen_company(seen, name):
                    continue
                jurisdiction_name = str(company.get("jurisdiction_code") or jurisdiction or "")
                results.append(
                    DiscoveredAccount(
                        account_id=stable_id("opencorporates", str(company.get("opencorporates_url") or company.get("company_number") or name)),
                        icp_id=icp.icp_id,
                        company_name=name,
                        website=str(company.get("opencorporates_url") or "") or None,
                        industry=str(company.get("company_type") or "registered company"),
                        location=jurisdiction_name.upper() if jurisdiction_name else "Unknown",
                        employee_count=0,
                        revenue_range=None,
                        source="opencorporates",
                        fit_score=0,
                        fit_reasons=["real OpenCorporates registry record"],
                        status="new",
                    )
                )
                if len(results) >= limit:
                    return results
        return results


@dataclass
class SECAccountProvider:
    user_agent: str
    tickers_url: str = "https://www.sec.gov/files/company_tickers.json"
    submissions_base_url: str = "https://data.sec.gov/submissions"
    timeout_seconds: float = 15.0
    max_submission_lookups: int = 15
    name: str = "sec_edgar"

    def search_accounts(
        self, icp: ICPDefinition, limit: int
    ) -> list[DiscoveredAccount]:
        if not self.user_agent.strip():
            return []
        response = requests.get(
            self.tickers_url,
            headers=self._headers(),
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        rows = list((response.json() or {}).values())
        terms = [term.lower() for term in search_terms(icp)]
        if not terms:
            return []
        candidates = [
            row
            for row in rows
            if not terms
            or any(term in str(row.get("title", "")).lower() for term in terms)
        ][: self.max_submission_lookups]
        results: list[DiscoveredAccount] = []
        for row in candidates:
            cik = int(row.get("cik_str", 0))
            if not cik:
                continue
            detail = requests.get(
                f"{self.submissions_base_url.rstrip('/')}/CIK{cik:010d}.json",
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
            detail.raise_for_status()
            payload = detail.json()
            addresses = payload.get("addresses") or {}
            business = addresses.get("business") or {}
            location = ", ".join(
                str(value)
                for value in (
                    business.get("stateOrCountryDescription"),
                    business.get("country"),
                )
                if value
            ) or "United States"
            results.append(
                DiscoveredAccount(
                    account_id=stable_id("sec", str(cik)),
                    icp_id=icp.icp_id,
                    company_name=str(payload.get("name") or row.get("title") or ""),
                    website=str(payload.get("website") or "") or None,
                    industry=str(payload.get("sicDescription") or "Public company"),
                    location=location,
                    employee_count=0,
                    revenue_range=None,
                    source="sec_edgar",
                    fit_score=0,
                    fit_reasons=[
                        "real SEC registrant",
                        f"CIK {cik:010d}",
                    ],
                    status="new",
                )
            )
            if len(results) >= limit:
                break
        return results

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
        }


@dataclass
class WebSearchAccountProvider:
    opensearch_web: Any
    collection: str = "sdr_prospect_discovery"
    timeout_seconds: float = 15.0
    name: str = "web_search"

    def search_accounts(
        self, icp: ICPDefinition, limit: int
    ) -> list[DiscoveredAccount]:
        if self.opensearch_web is None:
            return []
        results: list[DiscoveredAccount] = []
        seen: set[str] = set()
        for query in discovery_queries(icp):
            payload = self.opensearch_web.search(
                query=f'{query} official website OR site:linkedin.com/company',
                collection=self.collection,
                tenant_id="default",
                role="viewer",
                top_k=min(max(limit, 3), 6),
                provider=None,
                auto_fetch_and_index=True,
            )
            for hit in payload.get("hits", []) or payload.get("live_results", []) or []:
                url = str(hit.get("url") or "")
                title = _clean_company_name(str(hit.get("title") or ""))
                domain = str(hit.get("domain") or "") or _domain_from_url(url)
                if not _is_company_account_hit(title, url, domain):
                    continue
                if _seen_company(seen, title):
                    continue
                results.append(
                    DiscoveredAccount(
                        account_id=stable_id("web", url or title),
                        icp_id=icp.icp_id,
                        company_name=title,
                        website=url or None,
                        industry=", ".join(icp.account_criteria.industries[:2]) or "Web-discovered company",
                        location=", ".join(icp.account_criteria.geographies[:2]) or "Unknown",
                        employee_count=0,
                        revenue_range=None,
                        source="web_search",
                        fit_score=0,
                        fit_reasons=[
                            "company candidate discovered through SearchXNG/OpenSearch web search",
                            f"source domain: {domain}" if domain else "source domain unavailable",
                        ],
                        status="new",
                    )
                )
                if len(results) >= limit:
                    return results
        return results


@dataclass
class WebSearchContactProvider:
    opensearch_web: Any
    collection: str = "sdr_prospect_discovery"
    name: str = "web_search_public_contacts"

    def search_contacts(
        self,
        accounts: list[DiscoveredAccount],
        target_titles: list[str],
        target_seniorities: list[str],
    ) -> list[DiscoveredContact]:
        if self.opensearch_web is None:
            return []
        contacts: list[DiscoveredContact] = []
        seen: set[str] = set()
        titles = target_titles or ["VP Sales", "CRO", "Head of Sales", "Director of Revenue Operations"]
        for account in accounts:
            for title in titles[:2]:
                query = f'"{account.company_name}" "{title}" LinkedIn OR leadership OR team OR about'
                payload = self.opensearch_web.search(
                    query=query,
                    collection=self.collection,
                    tenant_id="default",
                    role="viewer",
                    top_k=4,
                    provider=None,
                    auto_fetch_and_index=True,
                )
                for hit in payload.get("hits", []) or payload.get("live_results", []) or []:
                    url = str(hit.get("url") or "")
                    text = " ".join(
                        str(hit.get(field) or "")
                        for field in ("title", "snippet", "content")
                    )
                    extracted = _extract_person_name_title(text, titles)
                    if not extracted:
                        continue
                    full_name, extracted_title = extracted
                    key = f"{account.account_id}:{full_name.lower()}:{extracted_title.lower()}"
                    if key in seen:
                        continue
                    seen.add(key)
                    seniority = "C-Suite" if extracted_title.upper() == "CRO" else "VP" if "vp" in extracted_title.lower() else "Director" if "director" in extracted_title.lower() else "Unknown"
                    contacts.append(
                        DiscoveredContact(
                            contact_id=stable_id("web_contact", key),
                            account_id=account.account_id,
                            full_name=full_name,
                            title=extracted_title,
                            department="Sales" if "sales" in extracted_title.lower() else "Revenue Operations",
                            seniority=seniority,
                            email=None,
                            linkedin_url=url if "linkedin.com/in/" in url else None,
                            phone=None,
                            email_verification_status="missing_public_email",
                            phone_verification_status="unknown",
                            contact_status="public_unverified",
                            is_former_employee=False,
                            confidence=45 if "linkedin.com/in/" in url else 35,
                            persona_match_score=80,
                            source="web_search_public",
                            status="needs_verification",
                        )
                    )
        return contacts


@dataclass
class CompositeAccountProvider:
    providers: list[AccountDiscoveryProvider] = field(default_factory=list)
    name: str = "public_composite"
    errors: list[str] = field(default_factory=list, init=False)

    def search_accounts(
        self, icp: ICPDefinition, limit: int
    ) -> list[DiscoveredAccount]:
        self.errors = []
        results: list[DiscoveredAccount] = []
        seen: set[str] = set()
        for provider in self.providers:
            try:
                candidates = provider.search_accounts(icp, limit)
            except Exception as exc:
                self.errors.append(f"{provider.name}: {exc}")
                continue
            for candidate in candidates:
                key = candidate.company_name.lower().strip()
                if key in seen:
                    continue
                seen.add(key)
                results.append(candidate)
                if len(results) >= limit:
                    return results
        return results


@dataclass
class NoPublicContactProvider:
    name: str = "none"

    def search_contacts(
        self,
        accounts: list[DiscoveredAccount],
        target_titles: list[str],
        target_seniorities: list[str],
    ) -> list[DiscoveredContact]:
        return []


_SYNTHETIC_FIRST_NAMES = ("Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley")
_SYNTHETIC_LAST_NAMES = ("Chen", "Patel", "Brooks", "Nguyen", "Reed", "Santos")


def _company_email_domain(account: DiscoveredAccount) -> str:
    if account.website:
        host = re.sub(r"^https?://", "", account.website.strip()).split("/")[0]
        if host.startswith("www."):
            host = host[4:]
        if host and "." in host:
            return host
    slug = re.sub(r"[^a-z0-9]+", "", account.company_name.lower()) or "company"
    return f"{slug}.example.com"


def _infer_seniority_from_title(title: str) -> str:
    lowered = title.lower()
    if any(token in lowered for token in ("ceo", "cro", "cmo", "cto", "coo", "chief")):
        return "C-Suite"
    if "vp" in lowered or "vice president" in lowered:
        return "VP"
    if "director" in lowered or "head of" in lowered:
        return "Director"
    if "manager" in lowered:
        return "Manager"
    return "Director"


@dataclass
class SyntheticContactProvider:
    """Persona placeholders for accounts when no verified public contact source exists."""

    name: str = "synthetic_persona"
    contacts_per_account: int = 2

    def search_contacts(
        self,
        accounts: list[DiscoveredAccount],
        target_titles: list[str],
        target_seniorities: list[str],
    ) -> list[DiscoveredContact]:
        titles = target_titles or [
            "VP Sales",
            "Director of Revenue Operations",
            "Head of Sales",
        ]
        contacts: list[DiscoveredContact] = []
        for account in accounts:
            domain = _company_email_domain(account)
            for idx, title in enumerate(titles[: self.contacts_per_account]):
                first = _SYNTHETIC_FIRST_NAMES[idx % len(_SYNTHETIC_FIRST_NAMES)]
                last = _SYNTHETIC_LAST_NAMES[
                    (idx + len(account.account_id)) % len(_SYNTHETIC_LAST_NAMES)
                ]
                full_name = f"{first} {last}"
                seniority = _infer_seniority_from_title(title)
                if target_seniorities and seniority not in target_seniorities:
                    continue
                email_local = f"{first.lower()}.{last.lower()}"
                key = f"{account.account_id}:{full_name}:{title}"
                persona_score = 70 if any(t.lower() in title.lower() for t in target_titles) else 55
                contacts.append(
                    DiscoveredContact(
                        contact_id=stable_id("syn_contact", key),
                        account_id=account.account_id,
                        full_name=full_name,
                        title=title,
                        department=(
                            "Sales"
                            if "sales" in title.lower()
                            else "Revenue Operations"
                        ),
                        seniority=seniority,
                        email=f"{email_local}@{domain}",
                        linkedin_url=None,
                        phone=None,
                        email_verification_status="synthetic_unverified",
                        phone_verification_status="unknown",
                        contact_status="synthetic_persona",
                        is_former_employee=False,
                        confidence=30,
                        persona_match_score=persona_score,
                        source="synthetic_persona",
                        status="needs_verification",
                    )
                )
        return contacts
