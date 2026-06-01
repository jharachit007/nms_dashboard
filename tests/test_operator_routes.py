from types import SimpleNamespace

from app.api.operator_routes import _alert_summary, _chat_message


def test_alert_summary_hides_ip_address_from_dashboard_payload() -> None:
    alert = SimpleNamespace(
        id=1,
        severity="CRITICAL",
        lifecycle_status="ACTIVE",
        last_event_time=None,
        first_event_time=None,
        created_at=None,
        node=SimpleNamespace(
            raw_label="airtel-delhi-10.20.30.40-web",
            operator="airtel",
            circle="delhi",
            server_type="web",
            ip_address="10.20.30.40",
        ),
    )

    payload = _alert_summary(alert)

    assert payload["node_name"] == "airtel-delhi-10.20.30.40-web"
    assert "ip_address" not in payload


def test_chat_message_returns_sanitized_message() -> None:
    message = SimpleNamespace(
        id=1,
        session_id=2,
        role="assistant",
        message="raw 10.20.30.40",
        sanitized_message="raw [IP]",
        provider="mock",
        created_at=None,
        advisory_only=True,
    )

    payload = _chat_message(message)

    assert payload["message"] == "raw [IP]"
