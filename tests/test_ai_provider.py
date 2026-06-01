from app.services.ai_provider import MockAIProvider, parse_recommendation_text


def test_mock_provider_returns_required_advisory_fields() -> None:
    response = MockAIProvider().generate("sanitized critical alert context")

    assert response.provider == "mock"
    assert response.recommendation["advisory_only"] is True
    assert response.recommendation["summary"]
    assert response.recommendation["probable_causes"]
    assert response.recommendation["troubleshooting_steps"]
    assert 0 <= response.confidence_score <= 1
    assert response.recommendation["suggested_next_checks"]


def test_parse_recommendation_text_clamps_confidence_and_forces_advisory_only() -> None:
    recommendation = parse_recommendation_text(
        """
        {
          "summary": "Check service health",
          "probable_causes": "Dependency failure",
          "troubleshooting_steps": ["Inspect recent events"],
          "confidence_score": 4.2,
          "suggested_next_checks": "Review node history",
          "advisory_only": false
        }
        """
    )

    assert recommendation["confidence_score"] == 1.0
    assert recommendation["probable_causes"] == ["Dependency failure"]
    assert recommendation["suggested_next_checks"] == ["Review node history"]
    assert recommendation["advisory_only"] is True
