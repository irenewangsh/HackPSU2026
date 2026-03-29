"""Layer 2 — Sensitivity Analyzer: classify data/context without storing secrets."""

import re
from urllib.parse import urlparse

from app.models.schemas import SensitivityLevel, SensitivityReport

_FIN = re.compile(
    r"\b(?:visa|mastercard|amex)\b|\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    re.I,
)
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_MONEY = re.compile(r"\$\s?\d+[.,]?\d*|\b\d+[.,]\d{2}\s?(?:USD|EUR)?\b", re.I)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_TOKEN = re.compile(r"\b(?:sk_live|Bearer\s+[a-zA-Z0-9._-]{20,})\b", re.I)

_ID_PATH = re.compile(
    r"passport|license|ssn|tax|w-?2|1099|bank|statement|invoice|payment|crypto|wallet",
    re.I,
)
_COURSE = re.compile(r"homework|assignment|cmpsc|cs\d{3}|course|lecture|\.pdf$", re.I)

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
                signals.append("URL host associated with money movement")
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
        return SensitivityReport(level=level, categories=categories, signals=signals)
