from dataclasses import dataclass

from app.connectors.opennms.client import OpenNMSXMLResponse
from app.services.ingestion_service import OpenNMSIngestionService


@dataclass
class StoredNode:
    id: int


class FakeDB:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeClient:
    def fetch_nodes(self) -> OpenNMSXMLResponse:
        return OpenNMSXMLResponse(
            resource="nodes",
            url="https://opennms.example/opennms/rest/nodes",
            status_code=200,
            raw_xml="""
            <nodes>
              <node id="42" label="airtel-delhi-10.20.30.40-web" />
              <node label="missing-id" />
            </nodes>
            """,
        )


class FakeNodeRepository:
    def __init__(self) -> None:
        self.values = []

    def upsert_by_opennms_id(self, values: dict) -> StoredNode:
        self.values.append(values)
        return StoredNode(id=101)


class FakeAuditService:
    def __init__(self) -> None:
        self.entries = []

    def record(self, **kwargs) -> None:
        self.entries.append(kwargs)


def test_ingestion_service_sync_nodes_upserts_and_audits_skipped_records() -> None:
    service = OpenNMSIngestionService.__new__(OpenNMSIngestionService)
    service.db = FakeDB()
    service.client = FakeClient()
    service.node_repository = FakeNodeRepository()
    service.audit_service = FakeAuditService()
    service._node_id_cache = {}

    result = service.sync_nodes()

    assert result.resource == "nodes"
    assert result.fetched_count == 2
    assert result.stored_count == 1
    assert result.skipped_count == 1
    assert result.errors
    assert service.node_repository.values[0]["opennms_id"] == "42"
    assert service._node_id_cache["42"] == 101
    assert service.audit_service.entries[0]["action"] == "opennms_ingestion_sync"
    assert service.db.commits == 1
    assert service.db.rollbacks == 0
