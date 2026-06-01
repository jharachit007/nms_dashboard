from app.services.node_label_parser import parse_node_label


def test_parse_node_label_extracts_required_segments() -> None:
    parsed = parse_node_label("airtel-delhi-10.20.30.40-web")

    assert parsed.raw_label == "airtel-delhi-10.20.30.40-web"
    assert parsed.operator == "airtel"
    assert parsed.circle == "delhi"
    assert parsed.ip_address == "10.20.30.40"
    assert parsed.server_type == "web"
    assert parsed.parse_error is None


def test_parse_node_label_preserves_raw_label_on_invalid_input() -> None:
    parsed = parse_node_label("invalid-label")

    assert parsed.raw_label == "invalid-label"
    assert parsed.operator is None
    assert parsed.parse_error is not None
