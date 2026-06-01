from app.services.sanitization import sanitize_for_llm


def test_sanitize_for_llm_masks_sensitive_values() -> None:
    raw = "host 10.0.0.1 owner noc@example.com token=abc123 password:supersecret"

    sanitized = sanitize_for_llm(raw, max_chars=500)

    assert "10.0.0.1" not in sanitized.text
    assert "noc@example.com" not in sanitized.text
    assert "abc123" not in sanitized.text
    assert "supersecret" not in sanitized.text
    assert "[IP]" in sanitized.text
    assert "[EMAIL]" in sanitized.text
    assert "[REDACTED]" in sanitized.text
    assert sanitized.truncated is False


def test_sanitize_for_llm_truncates_large_payloads() -> None:
    sanitized = sanitize_for_llm("x" * 20, max_chars=10)

    assert sanitized.text == "x" * 10 + "\n[TRUNCATED]"
    assert sanitized.truncated is True
