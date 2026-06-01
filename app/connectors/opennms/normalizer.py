from dataclasses import dataclass
from datetime import UTC, datetime
from xml.etree.ElementTree import Element

from app.connectors.opennms.xml_parser import (
    element_to_dict,
    element_to_raw_xml,
    iter_records,
    local_name,
    parse_xml_document,
)
from app.core.constants import AlertLifecycleStatus, AlertSeverity
from app.services.node_label_parser import parse_node_label


@dataclass(frozen=True)
class NormalizedBatch:
    records: list
    errors: list[str]


@dataclass(frozen=True)
class NormalizedRecord:
    opennms_id: str
    values: dict


@dataclass(frozen=True)
class NormalizedRelatedRecord:
    opennms_id: str
    opennms_node_id: str | None
    values: dict


def normalize_nodes(raw_xml: str) -> NormalizedBatch:
    return _normalize_batch(raw_xml, {"node"}, _normalize_node)


def normalize_alarms(raw_xml: str) -> NormalizedBatch:
    return _normalize_batch(raw_xml, {"alarm"}, _normalize_alarm)


def normalize_events(raw_xml: str) -> NormalizedBatch:
    return _normalize_batch(raw_xml, {"event"}, _normalize_event)


def normalize_outages(raw_xml: str) -> NormalizedBatch:
    return _normalize_batch(raw_xml, {"outage"}, _normalize_outage)


def _normalize_batch(raw_xml: str, record_names: set[str], normalizer) -> NormalizedBatch:
    root = parse_xml_document(raw_xml)
    records = []
    errors = []
    for element in iter_records(root, record_names):
        try:
            records.append(normalizer(element))
        except ValueError as exc:
            errors.append(str(exc))
    return NormalizedBatch(records=records, errors=errors)


def _normalize_node(element: Element) -> NormalizedRecord:
    opennms_id = _required_identifier(element, ("id", "nodeId", "nodeid", "foreignId"))
    raw_label = _first_value(element, ("label", "nodeLabel", "nodelabel", "foreignId")) or opennms_id
    parsed_label = parse_node_label(raw_label)
    normalized_payload = element_to_dict(element)
    if parsed_label.parse_error:
        normalized_payload["node_label_parse_error"] = parsed_label.parse_error

    return NormalizedRecord(
        opennms_id=opennms_id,
        values={
            "opennms_id": opennms_id,
            "raw_label": raw_label,
            "operator": parsed_label.operator,
            "circle": parsed_label.circle,
            "ip_address": parsed_label.ip_address,
            "server_type": parsed_label.server_type,
            "raw_xml": element_to_raw_xml(element),
            "normalized_payload": normalized_payload,
            "last_seen_at": _parse_datetime(_first_value(element, ("lastCapsdPoll", "lastSeen", "createTime"))),
        },
    )


def _normalize_alarm(element: Element) -> NormalizedRelatedRecord:
    opennms_id = _required_identifier(element, ("id", "alarmId", "alarmid"))
    opennms_node_id = _first_value(element, ("nodeId", "nodeid", "node-id"))
    severity = _normalize_severity(_first_value(element, ("severity",)))
    acknowledged_by = _first_value(element, ("alarmAckUser", "ackUser", "acknowledgedBy"))
    acknowledged_at = _parse_datetime(_first_value(element, ("alarmAckTime", "ackTime", "acknowledgedAt")))
    cleared_at = _parse_datetime(_first_value(element, ("clearTime", "clearedAt")))

    lifecycle_status = AlertLifecycleStatus.ACTIVE.value
    if cleared_at or severity in {AlertSeverity.NORMAL.value, "CLEARED"}:
        lifecycle_status = AlertLifecycleStatus.CLEARED.value
    elif acknowledged_by or acknowledged_at:
        lifecycle_status = AlertLifecycleStatus.ACKNOWLEDGED.value

    values = {
        "opennms_alarm_id": opennms_id,
        "severity": severity,
        "lifecycle_status": lifecycle_status,
        "uei": _first_value(element, ("uei",)),
        "log_message": _first_value(element, ("logMsg", "logmsg", "logMessage")),
        "description": _first_value(element, ("description", "descr")),
        "first_event_time": _parse_datetime(_first_value(element, ("firstEventTime", "firsteventtime"))),
        "last_event_time": _parse_datetime(_first_value(element, ("lastEventTime", "lasteventtime"))),
        "acknowledged_by": acknowledged_by,
        "acknowledged_at": acknowledged_at,
        "cleared_at": cleared_at,
        "raw_xml": element_to_raw_xml(element),
        "normalized_payload": element_to_dict(element),
    }
    return NormalizedRelatedRecord(opennms_id=opennms_id, opennms_node_id=opennms_node_id, values=values)


def _normalize_event(element: Element) -> NormalizedRelatedRecord:
    opennms_id = _required_identifier(element, ("id", "eventId", "eventid"))
    opennms_node_id = _first_value(element, ("nodeId", "nodeid", "node-id"))
    values = {
        "opennms_event_id": opennms_id,
        "uei": _first_value(element, ("uei",)),
        "severity": _normalize_optional_severity(_first_value(element, ("severity",))),
        "log_message": _first_value(element, ("logMsg", "logmsg", "logMessage")),
        "description": _first_value(element, ("description", "descr")),
        "event_time": _parse_datetime(_first_value(element, ("time", "eventTime", "eventtime", "createTime"))),
        "raw_xml": element_to_raw_xml(element),
        "normalized_payload": element_to_dict(element),
    }
    return NormalizedRelatedRecord(opennms_id=opennms_id, opennms_node_id=opennms_node_id, values=values)


def _normalize_outage(element: Element) -> NormalizedRelatedRecord:
    opennms_id = _required_identifier(element, ("id", "outageId", "outageid"))
    opennms_node_id = _first_value(element, ("nodeId", "nodeid", "node-id"))
    regained_service_at = _parse_datetime(_first_value(element, ("ifRegainedService", "regainedServiceAt")))
    status = AlertLifecycleStatus.CLEARED.value if regained_service_at else AlertLifecycleStatus.ACTIVE.value
    values = {
        "opennms_outage_id": opennms_id,
        "ip_address": _first_value(element, ("ipAddress", "ipaddr", "interfaceAddress")),
        "service_name": _first_value(element, ("serviceName", "service", "name")),
        "status": status,
        "lost_service_at": _parse_datetime(_first_value(element, ("ifLostService", "lostServiceAt"))),
        "regained_service_at": regained_service_at,
        "raw_xml": element_to_raw_xml(element),
        "normalized_payload": element_to_dict(element),
    }
    return NormalizedRelatedRecord(opennms_id=opennms_id, opennms_node_id=opennms_node_id, values=values)


def _required_identifier(element: Element, names: tuple[str, ...]) -> str:
    value = _first_value(element, names)
    if not value:
        raise ValueError(f"OpenNMS {local_name(element.tag)} record is missing identifier")
    return value


def _first_value(element: Element, names: tuple[str, ...]) -> str | None:
    lowered = {name.lower() for name in names}
    for key, value in element.attrib.items():
        if key.lower() in lowered and value.strip():
            return value.strip()

    for child in list(element):
        if local_name(child.tag).lower() in lowered:
            text = _text_content(child)
            if text:
                return text

    for child in element.iter():
        if child is element:
            continue
        if local_name(child.tag).lower() in lowered:
            text = _text_content(child)
            if text:
                return text
    return None


def _text_content(element: Element) -> str | None:
    text = "".join(element.itertext()).strip()
    return text or None


def _normalize_severity(value: str | None) -> str:
    if not value:
        return AlertSeverity.UNKNOWN.value
    normalized = value.strip().upper()
    if normalized == "CLEARED":
        return "CLEARED"
    try:
        return AlertSeverity(normalized).value
    except ValueError:
        return normalized


def _normalize_optional_severity(value: str | None) -> str | None:
    return _normalize_severity(value) if value else None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None

    if raw.isdigit():
        timestamp = int(raw)
        if timestamp > 9_999_999_999:
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp, tz=UTC)

    normalized = raw.replace("Z", "+00:00")
    if len(normalized) >= 5 and normalized[-5] in {"+", "-"} and normalized[-3] != ":":
        normalized = f"{normalized[:-2]}:{normalized[-2:]}"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
