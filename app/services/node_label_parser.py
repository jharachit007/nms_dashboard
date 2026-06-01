from dataclasses import dataclass
from ipaddress import ip_address


@dataclass(frozen=True)
class ParsedNodeLabel:
    raw_label: str
    operator: str | None
    circle: str | None
    ip_address: str | None
    server_type: str | None
    parse_error: str | None = None


def parse_node_label(raw_label: str) -> ParsedNodeLabel:
    parts = raw_label.split("-", 3)
    if len(parts) != 4:
        return ParsedNodeLabel(
            raw_label=raw_label,
            operator=None,
            circle=None,
            ip_address=None,
            server_type=None,
            parse_error="expected format {operator}-{circle}-{ip}-{server_type}",
        )

    operator, circle, node_ip, server_type = (part.strip() for part in parts)
    if not all((operator, circle, node_ip, server_type)):
        return ParsedNodeLabel(
            raw_label=raw_label,
            operator=operator or None,
            circle=circle or None,
            ip_address=node_ip or None,
            server_type=server_type or None,
            parse_error="node label contains empty segments",
        )

    try:
        parsed_ip = str(ip_address(node_ip))
    except ValueError:
        return ParsedNodeLabel(
            raw_label=raw_label,
            operator=operator,
            circle=circle,
            ip_address=node_ip,
            server_type=server_type,
            parse_error="node label IP segment is invalid",
        )

    return ParsedNodeLabel(
        raw_label=raw_label,
        operator=operator,
        circle=circle,
        ip_address=parsed_ip,
        server_type=server_type,
    )
