import re
from dataclasses import dataclass

_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_IPV4_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_SECRET_PATTERN = re.compile(
    r"(?i)\b(token|secret|password|passwd|api[_-]?key|authorization)\b\s*[:=]\s*([^\s,;]+)"
)


@dataclass(frozen=True)
class SanitizedText:
    text: str
    truncated: bool


def _mask_secret(match: re.Match) -> str:
    value = match.group(2)
    suffix = ""
    if value and value[-1] in ".,!?":
        suffix = value[-1]
    return f"{match.group(1)}=[REDACTED]{suffix}"


def sanitize_for_llm(value: str, max_chars: int) -> SanitizedText:
    sanitized = _SECRET_PATTERN.sub(_mask_secret, value)
    sanitized = _EMAIL_PATTERN.sub("[EMAIL]", sanitized)
    sanitized = _IPV4_PATTERN.sub("[IP]", sanitized)

    if len(sanitized) <= max_chars:
        return SanitizedText(text=sanitized, truncated=False)

    return SanitizedText(
        text=f"{sanitized[:max_chars]}\n[TRUNCATED]",
        truncated=True,
    )
