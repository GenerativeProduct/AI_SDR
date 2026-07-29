from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ai_sdr_platform.src.agents.prospect_discovery.models import (
    AccountDiscoveryResult,
    ContactDiscoveryResult,
    DiscoveredAccount,
    DiscoveredContact,
    DiscoveryRequest,
    ProspectDiscoveryRunResult,
)
from ai_sdr_platform.src.agents.prospect_discovery.repository import ProspectDiscoveryRepository
from ai_sdr_platform.src.agents.prospect_discovery.providers import (
    AccountDiscoveryProvider,
    ContactDiscoveryProvider,
)
from ai_sdr_platform.src.agents.prospect_discovery.identity import normalize_domain as _normalize_domain
from ai_sdr_platform.src.shared.config import settings

logger = logging.getLogger("sdr.prospect_discovery")


def icp_signature(icp) -> str:
    """Stable cache key from the ICP's account criteria (industries, geographies,
    employee range). Same criteria -> same signature -> reuse cached results."""
    crit = icp.account_criteria
    industries = sorted(v.strip().lower() for v in (crit.industries or []) if v.strip())
    geographies = sorted(v.strip().lower() for v in (crit.geographies or []) if v.strip())
    emp = crit.employee_range
    emp_key = f"{getattr(emp, 'min', None)}-{getattr(emp, 'max', None)}" if emp else "any"
    raw = "|".join(["ind:" + ",".join(industries), "geo:" + ",".join(geographies), "emp:" + emp_key])
    return hashlib.sha1(raw.encode()).hexdigest()[:16]

MOCK_COMPANIES = [
    {"account_id": "acc_001", "company_name": "Acme SaaS", "website": "https://acmesaas.com", "linkedin_url": "https://linkedin.com/company/acme-saas", "industry": "SaaS", "location": "North America", "employee_count": 320, "revenue_range": "mid-market"},
    {"account_id": "acc_002", "company_name": "Global FinTech", "website": "https://globalfintech.io", "linkedin_url": "https://linkedin.com/company/global-fintech", "industry": "FinTech", "location": "Europe", "employee_count": 800, "revenue_range": "enterprise"},
    {"account_id": "acc_003", "company_name": "Health Track", "website": "https://healthtrack.io", "linkedin_url": "https://linkedin.com/company/health-track", "industry": "HealthTech", "location": "APAC", "employee_count": 120, "revenue_range": "smb"},
    {"account_id": "acc_004", "company_name": "Shopify Masters", "website": "https://shopifymasters.com", "linkedin_url": "https://linkedin.com/company/shopify-masters", "industry": "E-Commerce", "location": "North America", "employee_count": 45, "revenue_range": "smb"},
    {"account_id": "acc_005", "company_name": "CloudNova", "website": "https://cloudnova.com", "linkedin_url": "https://linkedin.com/company/cloudnova", "industry": "SaaS", "location": "Europe", "employee_count": 1500, "revenue_range": "enterprise"},
]

_MOCK_CONTACTS = {
    "acc_001": [
        {"full_name": "Sarah Chen", "title": "VP Sales", "department": "Sales", "seniority": "VP", "email": "sarah.chen@acmesaas.com", "linkedin_url": "linkedin.com/in/sarah-chen", "phone": "+1-415-555-0101", "email_verification_status": "verified", "phone_verification_status": "verified", "contact_status": "active", "is_former_employee": False},
        {"full_name": "David Park", "title": "Director of Revenue Ops", "department": "RevOps", "seniority": "Director", "email": "david.park@acmesaas.com", "linkedin_url": "linkedin.com/in/david-park", "phone": None, "email_verification_status": "verified", "phone_verification_status": "unknown", "contact_status": "active", "is_former_employee": False},
    ],
    "acc_002": [
        {"full_name": "James Okafor", "title": "CRO", "department": "Sales", "seniority": "C-Suite", "email": "james.okafor@globalft.com", "linkedin_url": "linkedin.com/in/james-okafor", "phone": "+44-20-7946-0958", "email_verification_status": "verified", "phone_verification_status": "verified", "contact_status": "active", "is_former_employee": False},
        {"full_name": "Nina Patel", "title": "Head of Marketing", "department": "Marketing", "seniority": "VP", "email": "nina.patel@globalft.com", "linkedin_url": "linkedin.com/in/nina-patel", "phone": None, "email_verification_status": "unverified", "phone_verification_status": "unknown", "contact_status": "active", "is_former_employee": False},
    ],
    "acc_003": [
        {"full_name": "Dr. Priya Roy", "title": "CEO", "department": "Executive", "seniority": "C-Suite", "email": "priya.roy@healthtrack.io", "linkedin_url": "linkedin.com/in/priya-roy", "phone": "+91-98765-43210", "email_verification_status": "verified", "phone_verification_status": "verified", "contact_status": "active", "is_former_employee": False},
        {"full_name": "Tom Briggs", "title": "VP of Partnerships", "department": "Sales", "seniority": "VP", "email": "tom.briggs@healthtrack.io", "linkedin_url": "linkedin.com/in/tom-briggs", "phone": None, "email_verification_status": "catch_all", "phone_verification_status": "unknown", "contact_status": "active", "is_former_employee": False},
    ],
    "acc_004": [
        {"full_name": "Marco Rossi", "title": "Head of Growth", "department": "Marketing", "seniority": "Director", "email": "marco.rossi@shopifymasters.com", "linkedin_url": "linkedin.com/in/marco-rossi", "phone": "+1-212-555-0199", "email_verification_status": "verified", "phone_verification_status": "unverified", "contact_status": "active", "is_former_employee": False},
    ],
    "acc_005": [
        {"full_name": "Priya Nair", "title": "Director, Demand Gen", "department": "Marketing", "seniority": "Director", "email": "priya.nair@cloudnova.com", "linkedin_url": "linkedin.com/in/priya-nair", "phone": None, "email_verification_status": "verified", "phone_verification_status": "unknown", "contact_status": "active", "is_former_employee": False},
        {"full_name": "Kenji Yamamoto", "title": "Head of RevOps", "department": "RevOps", "seniority": "Director", "email": "kenji.y@cloudnova.com", "linkedin_url": "linkedin.com/in/kenji-yamamoto", "phone": "+49-30-1234-5678", "email_verification_status": "verified", "phone_verification_status": "verified", "contact_status": "active", "is_former_employee": False},
    ],
}

_SENIORITY_RANK = {"C-Suite": 100, "VP": 85, "Director": 70, "Manager": 50, "IC": 30}
_TITLE_SENIORITY_MAP = {
    "ceo": "C-Suite", "cro": "C-Suite", "cmo": "C-Suite", "cto": "C-Suite", "coo": "C-Suite",
    "vp": "VP", "vice president": "VP", "director": "Director", "head of": "Director", "manager": "Manager",
}


@dataclass
class ProspectDiscoveryService:
    repository: ProspectDiscoveryRepository
    account_provider: AccountDiscoveryProvider | None = None
    contact_provider: ContactDiscoveryProvider | None = None
    email_providers: list = field(default_factory=list)  # waterfall: Hunter, etc.

    def _apply_email_waterfall(
        self, contacts: list[DiscoveredContact], accounts: list
    ) -> None:
        """Fill missing emails and verify unverified ones using the available
        email providers in priority order (stop at first confident result)."""
        providers = [p for p in self.email_providers if getattr(p, "is_available", lambda: False)()]
        if not providers or not contacts:
            return
        domain_by_account = {
            a.account_id: _normalize_domain(getattr(a, "website", None))
            for a in accounts
        }
        found, verified = 0, 0
        for contact in contacts:
            domain = domain_by_account.get(contact.account_id)
            if not contact.email and domain:
                for provider in providers:
                    result = provider.find_email(contact.full_name, domain)
                    if result and result.email:
                        contact.email = result.email
                        contact.email_verification_status = result.status or "unverified"
                        contact.source = f"{contact.source}+{provider.name}"
                        found += 1
                        break
            elif contact.email and contact.email_verification_status != "verified":
                for provider in providers:
                    status = provider.verify_email(contact.email)
                    if status:
                        contact.email_verification_status = status
                        contact.source = f"{contact.source}+{provider.name}"
                        verified += 1
                        break
        logger.info(
            "Email waterfall: %d emails found, %d verified (providers=%s)",
            found, verified, ",".join(p.name for p in providers),
        )

    def discover_accounts(self, request: DiscoveryRequest) -> AccountDiscoveryResult:
        if self.account_provider is not None:
            return self._discover_provider_accounts(request)
        icp = request.icp_definition
        results: list[DiscoveredAccount] = []
        target_industries = icp.account_criteria.industries
        target_geographies = icp.account_criteria.geographies
        emp_range = icp.account_criteria.employee_range
        exclusions = icp.exclusions.model_dump()
        excluded_industries = [str(item).lower() for item in exclusions.get("industries", [])]
        excluded_companies = [str(item).lower() for item in exclusions.get("company_names", [])]
        excluded_geographies = [str(item).lower() for item in exclusions.get("geographies", [])]
        min_employee_threshold = exclusions.get("employee_max_below")

        for comp in MOCK_COMPANIES:
            fit_score = 0
            fit_reasons: list[str] = []
            company_name_lower = comp["company_name"].lower()
            location_lower = comp["location"].lower()
            industry_lower = comp["industry"].lower()

            if industry_lower in excluded_industries or company_name_lower in excluded_companies:
                continue
            if excluded_geographies and any(geo in location_lower for geo in excluded_geographies):
                continue
            if min_employee_threshold is not None and comp["employee_count"] < min_employee_threshold:
                continue

            if target_industries:
                if any(ind.lower() in industry_lower for ind in target_industries):
                    fit_score += 40
                    fit_reasons.append("industry match")
            else:
                fit_score += 40

            if target_geographies:
                if any(geo.lower() in location_lower for geo in target_geographies):
                    fit_score += 30
                    fit_reasons.append("geography match")
            else:
                fit_score += 30

            if emp_range:
                min_emp = emp_range.min or 0
                max_emp = emp_range.max or float("inf")
                if min_emp <= comp["employee_count"] <= max_emp:
                    fit_score += 30
                    fit_reasons.append("employee size match")
            else:
                fit_score += 30

            if fit_score <= 0:
                continue

            account = DiscoveredAccount(
                **comp,
                icp_id=icp.icp_id,
                fit_score=fit_score,
                fit_reasons=fit_reasons,
                source="mock",
                status="new",
            )
            if self._is_duplicate_account(results, account):
                continue
            self.repository.save_account(account)
            results.append(account)

        results.sort(key=lambda item: item.fit_score, reverse=True)
        final_results = results[: request.limit]
        return AccountDiscoveryResult(accounts=final_results, total=len(results))

    def discover_contacts(
        self,
        account_ids: list[str],
        target_titles: list[str] | None = None,
        target_seniorities: list[str] | None = None,
    ) -> ContactDiscoveryResult:
        if self.contact_provider is not None:
            account_id_set = set(account_ids)
            accounts = [
                account
                for account in self.repository.list_accounts()
                if account.account_id in account_id_set
            ]

            # Cache-first: reuse fresh contacts already discovered for these
            # accounts, and only call the external API for accounts we don't have
            # fresh contacts for.
            cached_contacts: list[DiscoveredContact] = []
            accounts_to_fetch = accounts
            if self._cache_enabled():
                cached_contacts = self.repository.find_contacts_by_accounts(
                    list(account_id_set), self._cache_cutoff()
                )
                have_fresh = {c.account_id for c in cached_contacts}
                accounts_to_fetch = [a for a in accounts if a.account_id not in have_fresh]

            fetched: list[DiscoveredContact] = []
            if accounts_to_fetch:
                fetched = self.contact_provider.search_contacts(
                    accounts_to_fetch,
                    target_titles or [],
                    target_seniorities or [],
                )
                # Waterfall: enrich/verify emails via Hunter (etc.) before saving.
                self._apply_email_waterfall(fetched, accounts_to_fetch)
                for contact in fetched:
                    self.repository.save_contact(contact)

            logger.info(
                "Contact discovery: %d from cache, %d from API (%d accounts fetched)",
                len(cached_contacts), len(fetched), len(accounts_to_fetch),
            )
            contacts = cached_contacts + fetched
            contacts.sort(
                key=lambda item: (item.persona_match_score, item.confidence),
                reverse=True,
            )
            return ContactDiscoveryResult(contacts=contacts, total=len(contacts))
        results: list[DiscoveredContact] = []
        target_titles_lower = [title.lower() for title in (target_titles or [])]
        target_seniorities_norm = [seniority.strip() for seniority in (target_seniorities or [])]

        for account_id in account_ids:
            mock_list = _MOCK_CONTACTS.get(account_id, [])
            for idx, contact in enumerate(mock_list):
                contact_id = f"con_{account_id.replace('acc_', '')}_{idx + 1:02d}"
                title = contact["title"]
                seniority = contact.get("seniority") or self._infer_seniority(title)
                confidence = 75 + (10 if contact.get("email") else 0) + (5 if contact.get("linkedin_url") else 0)
                confidence = min(confidence, 100)
                persona_score = 0
                if target_titles_lower:
                    if any(keyword in title.lower() for keyword in target_titles_lower):
                        persona_score += 60
                else:
                    persona_score += 60

                if target_seniorities_norm:
                    if seniority in target_seniorities_norm:
                        persona_score += 40
                else:
                    persona_score += _SENIORITY_RANK.get(seniority, 30) * 40 // 100
                persona_score = min(persona_score, 100)

                record = DiscoveredContact(
                    contact_id=contact_id,
                    account_id=account_id,
                    full_name=contact["full_name"],
                    title=title,
                    department=contact.get("department", ""),
                    seniority=seniority,
                    email=contact.get("email", ""),
                    linkedin_url=contact.get("linkedin_url", ""),
                    phone=contact.get("phone"),
                    email_verification_status=contact.get("email_verification_status", "unknown"),
                    phone_verification_status=contact.get("phone_verification_status", "unknown"),
                    contact_status=contact.get("contact_status", "active"),
                    is_former_employee=contact.get("is_former_employee", False),
                    confidence=confidence,
                    persona_match_score=persona_score,
                    source="mock",
                    status="new",
                )
                if self._is_duplicate_contact(results, record):
                    continue
                self.repository.save_contact(record)
                results.append(record)

        results.sort(key=lambda item: (item.persona_match_score, item.confidence), reverse=True)
        return ContactDiscoveryResult(contacts=results, total=len(results))

    def run_full_discovery(self, request: DiscoveryRequest) -> ProspectDiscoveryRunResult:
        accounts_result = self.discover_accounts(request)
        contacts_result = self.discover_contacts(
            account_ids=[account.account_id for account in accounts_result.accounts],
            target_titles=request.icp_definition.persona_criteria.titles,
            target_seniorities=request.icp_definition.persona_criteria.seniorities,
        )
        return ProspectDiscoveryRunResult(
            accounts=accounts_result.accounts,
            contacts=contacts_result.contacts,
            account_total=accounts_result.total,
            contact_total=contacts_result.total,
        )

    def _discover_provider_accounts(
        self, request: DiscoveryRequest
    ) -> AccountDiscoveryResult:
        icp = request.icp_definition
        signature = icp_signature(icp)
        results: list[DiscoveredAccount] = []

        # 1) Cache-first: reuse fresh accounts previously discovered for this ICP.
        cached_count = 0
        if self._cache_enabled():
            cutoff = self._cache_cutoff()
            for cached in self.repository.find_accounts_by_signature(signature, cutoff):
                if self._is_excluded(cached, icp) or self._is_duplicate_account(results, cached):
                    continue
                cached.icp_id = icp.icp_id
                results.append(cached)
            cached_count = len(results)

        # 2) Only call the external API for the remaining gap.
        api_count = 0
        if len(results) < request.limit:
            candidates = self.account_provider.search_accounts(icp, request.limit * 3)
            for candidate in candidates:
                score, reasons = self._score_account(candidate, icp)
                candidate.fit_score = score
                candidate.fit_reasons = list(
                    dict.fromkeys([*candidate.fit_reasons, *reasons])
                )
                if score <= 0 or self._is_excluded(candidate, icp):
                    continue
                if self._is_duplicate_account(results, candidate):
                    continue
                self.repository.save_account(candidate, icp_signature=signature)
                results.append(candidate)
                api_count += 1

        logger.info(
            "Account discovery: %d from cache, %d from API (signature=%s)",
            cached_count, api_count, signature,
        )
        results.sort(key=lambda item: item.fit_score, reverse=True)
        return AccountDiscoveryResult(
            accounts=results[: request.limit],
            total=len(results),
        )

    @staticmethod
    def _cache_enabled() -> bool:
        return bool(getattr(settings, "discovery_cache_enabled", True))

    @staticmethod
    def _cache_cutoff() -> datetime:
        # Naive UTC to match the naive DateTime columns (avoids tz-mismatch in the
        # SQL comparison on Postgres).
        days = int(getattr(settings, "cache_ttl_days", 30))
        return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    @staticmethod
    def _score_account(account: DiscoveredAccount, icp) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        industries = [value.lower() for value in icp.account_criteria.industries]
        geographies = [value.lower() for value in icp.account_criteria.geographies]
        industry = account.industry.lower()
        location = account.location.lower()

        # Apollo applies the industry, location and employee filters server-side,
        # so its results already satisfy the ICP. Apollo's company-search payload
        # frequently omits parsed industry/city/state/country (they come back as
        # "Unknown"), which would fail the local string checks below and wrongly
        # discard every real company. Trust the provider's own filtering instead.
        provider_filtered = account.source == "apollo"

        if industries:
            if any(value in industry for value in industries):
                score += 40
                reasons.append("industry match")
            elif provider_filtered:
                score += 40
                reasons.append("industry matched via Apollo keyword filters")
            elif account.source in {
                "gleif",
                "sec_edgar",
                "companies_house",
                "opencorporates",
                "web_search",
            }:
                score += 20
                reasons.append("public source keyword candidate; industry needs enrichment")
        else:
            score += 40

        if geographies:
            if ProspectDiscoveryService._geography_matches(location, geographies):
                score += 30
                reasons.append("geography match")
            elif provider_filtered:
                score += 30
                reasons.append("geography matched via Apollo location filters")
            else:
                return 0, ["geography did not match the ICP"]
        else:
            score += 30

        employee_range = icp.account_criteria.employee_range
        if employee_range and account.employee_count > 0:
            minimum = employee_range.min or 0
            maximum = employee_range.max or float("inf")
            if minimum <= account.employee_count <= maximum:
                score += 30
                reasons.append("employee size match")
        elif employee_range is None:
            score += 30
        else:
            reasons.append("employee count unavailable; verify during enrichment")
        return min(score, 100), reasons

    @staticmethod
    def _geography_matches(location: str, targets: list[str]) -> bool:
        country_aliases = {
            "united states": {"us", "usa", "united states", "us_wa", "us_ca", "us_ny", "us_tx", "us_de"},
            "washington": {"wa", "washington", "us_wa", "washington, united states"},
            "united kingdom": {"gb", "uk", "united kingdom", "great britain"},
            "india": {"in", "india"},
            "canada": {"ca", "canada"},
        }
        europe_codes = {
            "at", "be", "bg", "hr", "cy", "cz", "de", "dk", "ee", "es", "fi",
            "fr", "gr", "hu", "ie", "is", "it", "li", "lt", "lu", "lv", "mt",
            "nl", "no", "pl", "pt", "ro", "se", "si", "sk", "ch", "gb",
        }
        location_value = location.lower().strip()
        for target in targets:
            normalized = target.lower().strip()
            if normalized in location_value:
                return True
            if location_value in normalized:
                return True
            aliases = country_aliases.get(normalized)
            if aliases and (location_value in aliases or any(alias in location_value for alias in aliases)):
                return True
            if normalized == "europe" and (
                location_value in europe_codes or "europe" in location_value
            ):
                return True
        return False

    @staticmethod
    def _is_excluded(account: DiscoveredAccount, icp) -> bool:
        exclusions = icp.exclusions
        company_name = account.company_name.lower()
        industry = account.industry.lower()
        location = account.location.lower()
        if any(value.lower() in industry for value in exclusions.industries):
            return True
        if any(value.lower() == company_name for value in exclusions.company_names):
            return True
        if any(value.lower() in location for value in exclusions.geographies):
            return True
        if (
            exclusions.employee_max_below is not None
            and account.employee_count > 0
            and account.employee_count < exclusions.employee_max_below
        ):
            return True
        return False

    @staticmethod
    def _is_duplicate_account(existing_accounts: list[DiscoveredAccount], account: DiscoveredAccount) -> bool:
        for existing in existing_accounts:
            if existing.company_name.lower() == account.company_name.lower():
                return True
            if account.website and existing.website and existing.website.lower() == account.website.lower():
                return True
        return False

    @staticmethod
    def _is_duplicate_contact(existing_contacts: list[DiscoveredContact], contact: DiscoveredContact) -> bool:
        for existing in existing_contacts:
            if existing.full_name.lower() == contact.full_name.lower() and existing.account_id == contact.account_id:
                return True
        return False

    def _infer_seniority(self, title: str) -> str:
        lowered = title.lower()
        for keyword, level in _TITLE_SENIORITY_MAP.items():
            if keyword in lowered:
                return level
        return "IC"
