"""Layer 2 — Sensitivity Analyzer: classify data/context without storing secrets."""

import re
from urllib.parse import urlparse

from app.models.schemas import DomainTrust, SensitivityLevel, SensitivityReport

_FIN = re.compile(
    r"\b(?:visa|mastercard|amex)\b|\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    re.I,
)
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_MONEY = re.compile(r"\$\s?\d+[.,]?\d*|\b\d+[.,]\d{2}\s?(?:USD|EUR)?\b", re.I)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_TOKEN = re.compile(r"\b(?:sk_live|Bearer\s+[a-zA-Z0-9._-]{20,})\b", re.I)
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_APIKEY = re.compile(r"\b(?:api[_-]?key|token|secret|credential)\b", re.I)

_ID_PATH = re.compile(
    r"passport|license|ssn|tax|w-?2|1099|bank|statement|invoice|payment|crypto|wallet",
    re.I,
)
_COURSE = re.compile(r"homework|assignment|cmpsc|cs\d{3}|course|lecture|\.pdf$", re.I)
_CTX_FIN = re.compile(
    r"\bbank|payment|invoice|refund|transfer|credit|debit|billing|amount\b", re.I
)
_CTX_ID = re.compile(r"\bpassport|ssn|license|visa|student id|student_id\b", re.I)
_CTX_AUTH = re.compile(
    r"\bpassword|otp|2fa|login|credential|secret|auth\b", re.I
)
_CTX_COURSE = re.compile(r"\bhomework|assignment|lab|cmpsc|cmpen|canvas\b", re.I)

_HIGH_DOMAINS = (
    "bank",
    "paypal",
    "stripe",
    "venmo",
    "coinbase",
    "schwab",
    "chase",
    "wellsfargo",
)
_TRUSTED_DOMAINS = (
    "psu.edu",
    "canvas.psu.edu",
    "github.com",
)
_AUTH_FIELDS = ("password", "passwd", "ssn", "card", "cvv", "routing", "account")


class SensitivityAnalyzer:
    def analyze(
        self,
        *,
        path: str | None,
        url: str | None,
        mime: str | None,
        text: str | None,
        form_fields: list[str] | None,
    ) -> SensitivityReport:
        signals: list[str] = []
        categories: list[str] = []
        score = 0
        domain_trust = DomainTrust.UNTRUSTED

        if path:
            lp = path.lower()
            if _COURSE.search(lp):
                categories.append("coursework")
                score += 1
                signals.append("path looks like coursework")
            if _ID_PATH.search(lp):
                categories.append("identity_or_finance")
                score += 3
                signals.append("path suggests identity or financial docs")

        host = ""
        if url:
            try:
                host = urlparse(url).netloc.lower()
            except Exception:
                host = ""
            if any(h in host for h in _HIGH_DOMAINS):
                categories.append("financial_surface")
                score += 4
                domain_trust = DomainTrust.FINANCIAL
                signals.append("URL host associated with money movement")
            elif any(host == d or host.endswith(f".{d}") for d in _TRUSTED_DOMAINS):
                domain_trust = DomainTrust.TRUSTED
                signals.append("URL host on trusted allowlist")
            if "login" in url.lower() or "signin" in url.lower() or "oauth" in url.lower():
                categories.append("authentication")
                score += 2
                signals.append("URL suggests authentication flow")

        if mime:
            ml = mime.lower()
            if ml in ("application/pdf",):
                score += 1
                signals.append("binary document MIME")

        blob = (text or "")[:8000]
        if _FIN.search(blob) or _SSN.search(blob):
            categories.append("structured_id")
            score += 4
            signals.append("possible card/SSN pattern in preview")
        if _PHONE.search(blob):
            categories.append("identity_or_finance")
            score += 2
            signals.append("possible phone number in preview")
        if _MONEY.search(blob):
            categories.append("monetary")
            score += 2
            signals.append("monetary amounts in preview")
        if _EMAIL.search(blob):
            score += 1
            signals.append("email-like tokens in preview")
        if _TOKEN.search(blob):
            categories.append("secret_material")
            score += 5
            signals.append("credential/API token pattern in preview")
        if _APIKEY.search(blob):
            categories.append("secret_material")
            score += 2
            signals.append("auth keyword context detected")
        if _CTX_FIN.search(blob):
            categories.append("financial_surface")
            score += 2
            signals.append("financial context keywords detected")
        if _CTX_ID.search(blob):
            categories.append("identity_or_finance")
            score += 2
            signals.append("identity context keywords detected")
        if _CTX_AUTH.search(blob):
            categories.append("authentication")
            score += 2
            signals.append("authentication context keywords detected")
        if _CTX_COURSE.search(blob):
            categories.append("coursework")
            score += 1
            signals.append("coursework context keywords detected")

        if form_fields:
            fl = [f.lower() for f in form_fields]
            if any(x in " ".join(fl) for x in _AUTH_FIELDS):
                categories.append("sensitive_form")
                score += 3
                signals.append("form fields suggest auth or payment")

        if score <= 1:
            level = SensitivityLevel.LOW
        elif score <= 4:
            level = SensitivityLevel.MEDIUM
        elif score <= 7:
            level = SensitivityLevel.HIGH
        else:
            level = SensitivityLevel.CRITICAL

        categories = sorted(set(categories))
        return SensitivityReport(
            level=level,
            domain_trust=domain_trust,
            categories=categories,
            signals=signals,
        )
