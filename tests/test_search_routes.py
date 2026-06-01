from app.api.search_routes import _serialize_result


def test_serialize_search_result_includes_resolution_context() -> None:
    payload = _serialize_result(
        {
            "id": 1,
            "alert_id": 2,
            "node_id": 3,
            "content_text": "sanitized incident",
            "metadata": {"source": "alert"},
            "distance": 0.12,
            "ai_recommendation": {"summary": "check"},
            "feedback_type": "Helpful",
            "resolution_status": "Resolved",
            "created_at": None,
        }
    )

    assert payload["distance"] == 0.12
    assert payload["feedback_type"] == "Helpful"
    assert payload["resolution_status"] == "Resolved"
