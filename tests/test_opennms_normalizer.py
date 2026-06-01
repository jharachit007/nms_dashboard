from app.connectors.opennms.normalizer import (
    normalize_alarms,
    normalize_events,
    normalize_nodes,
    normalize_outages,
)
from app.core.constants import AlertLifecycleStatus


def test_normalize_nodes_extracts_label_metadata_and_preserves_raw_xml() -> None:
    batch = normalize_nodes(
        """
        <nodes>
          <node id="42" label="airtel-delhi-10.20.30.40-web">
            <foreignId>node-42</foreignId>
            <createTime>2026-06-01T12:00:00Z</createTime>
          </node>
        </nodes>
        """
    )

    assert batch.errors == []
    assert len(batch.records) == 1
    values = batch.records[0].values
    assert values["opennms_id"] == "42"
    assert values["raw_label"] == "airtel-delhi-10.20.30.40-web"
    assert values["operator"] == "airtel"
    assert values["circle"] == "delhi"
    assert values["ip_address"] == "10.20.30.40"
    assert values["server_type"] == "web"
    assert "<node" in values["raw_xml"]
    assert values["normalized_payload"]["tag"] == "node"


def test_normalize_alarms_maps_acknowledged_status() -> None:
    batch = normalize_alarms(
        """
        <alarms>
          <alarm id="100" severity="CRITICAL" nodeId="42">
            <uei>uei.opennms.org/test</uei>
            <logMsg>Interface down</logMsg>
            <alarmAckUser>noc-user</alarmAckUser>
          </alarm>
        </alarms>
        """
    )

    assert batch.errors == []
    alarm = batch.records[0]
    assert alarm.opennms_node_id == "42"
    assert alarm.values["opennms_alarm_id"] == "100"
    assert alarm.values["severity"] == "CRITICAL"
    assert alarm.values["lifecycle_status"] == AlertLifecycleStatus.ACKNOWLEDGED.value
    assert alarm.values["uei"] == "uei.opennms.org/test"


def test_normalize_events_and_outages_handle_missing_optional_fields() -> None:
    events = normalize_events(
        """
        <events>
          <event id="200">
            <nodeid>42</nodeid>
            <uei>uei.opennms.org/event</uei>
          </event>
        </events>
        """
    )
    outages = normalize_outages(
        """
        <outages>
          <outage id="300" nodeId="42">
            <ipAddress>10.20.30.40</ipAddress>
            <serviceName>HTTP</serviceName>
            <ifLostService>2026-06-01T12:00:00+0000</ifLostService>
          </outage>
        </outages>
        """
    )

    assert events.errors == []
    assert events.records[0].values["opennms_event_id"] == "200"
    assert events.records[0].values["severity"] is None
    assert outages.errors == []
    assert outages.records[0].values["opennms_outage_id"] == "300"
    assert outages.records[0].values["status"] == AlertLifecycleStatus.ACTIVE.value


def test_normalizers_skip_records_missing_required_identifiers() -> None:
    batch = normalize_nodes("<nodes><node label=\"missing-id\" /></nodes>")

    assert batch.records == []
    assert batch.errors
