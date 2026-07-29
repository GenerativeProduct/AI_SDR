"""Canonical identity keys for cross-source de-duplication.

Two providers (Apollo, Hunter, ZoomInfo, public registries) can return the same
real-world company or person with different source ids. To store exactly one row
per real-world entity, we compute a *canonical key* that is independent of the
source, and de-duplicate/merge on that key.

- Company key:  normalized domain  ->  else  "name:<slug>"
- Contact key:  "email:<lower>"  ->  else "li:<linkedin>"  ->  else "name:<name>@@<company>"
"""

from __future__ import annotations

import re

# Registry / aggregator domains that are NOT a company's own site. A website of
# opencorporates.com does not identify a real company, so it must not become a key.
_NON_COMPANY_DOMAINS = {
    "opencorporates.com",
    "gleif.org",
    "sec.gov",
    "find-and-update.company-information.service.gov.uk",
    "company-information.service.gov.uk",
    "linkedin.com",
    "crunchbase.com",
    "facebook.com",
    "twitter.com",
    "x.com",
}


def normalize_domain(website: str | None) -> str | None:
    """Extract a clean company domain from a URL/host, or None if unusable."""
    if not website:
        return None
    host = re.sub(r"^https?://", "", str(website).strip().lower()).split("/")[0]
    host = host.split("?")[0].strip()
    if host.startswith("www."):
        host = host[4:]
    if not host or "." not in host:
        return None
    if host.endswith(".example.com") or host in _NON_COMPANY_DOMAINS:
        return None
    return host


def slug(text: str | None) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return cleaned or "unknown"


def normalize_linkedin(url: str | None) -> str | None:
    """Reduce a LinkedIn URL to its stable path (e.g. 'in/meg-murray-9a2a30a')."""
    if not url:
        return None
    u = re.sub(r"^https?://", "", str(url).strip().lower())
    u = re.sub(r"^([a-z]{2,3}\.)?linkedin\.com/", "", u)  # drop host + country sub
    u = u.split("?")[0].rstrip("/")
    return u or None


def company_key(company_name: str | None, website: str | None) -> str:
    """Canonical company identity: domain if we have a real one, else name slug."""
    domain = normalize_domain(website)
    if domain:
        return f"domain:{domain}"
    return f"name:{slug(company_name)}"


def contact_key(
    email: str | None,
    linkedin_url: str | None,
    full_name: str | None,
    company_ref: str | None,
) -> str:
    """Canonical contact identity. Strongest available signal wins.

    `company_ref` is the contact's company key (or account id) — used only for the
    weak name-based fallback so two different "John Smith"s at different companies
    stay distinct.
    """
    if email and email.strip():
        return f"email:{email.strip().lower()}"
    li = normalize_linkedin(linkedin_url)
    if li:
        return f"li:{li}"
    return f"name:{slug(full_name)}@@{company_ref or 'unknown'}"
