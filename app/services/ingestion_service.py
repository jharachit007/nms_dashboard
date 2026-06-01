import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.connectors.opennms.client import OpenNMSClient
from app.connectors.opennms.normalizer import (
    NormalizedBatch,
    NormalizedRecord,
    NormalizedRelatedRecord,
    normalize_alarms,
    normalize_events,
    normalize_nodes,
    normalize_outages,
)
from app.core.constants import AlertLifecycleStatus
from app.models.alert import AlertHistory
from app.repositories.alert_repository import AlertRepository
from app.repositories.event_repository import EventRepository
from app.repositories.node_repository import NodeRepository
from app.repositories.outage_repository import OutageRepository
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionResourceResult:
    resource: str
    fetched_count: int = 0
    stored_count: int = 0
    skipped_count: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class IngestionRunResult:
    resources: dict[str, IngestionResourceResult]

    @property
    def success(self) -> bool:
        return all(result.success for result in self.resources.values())


class OpenNMSIngestionService:
    def __init__(self, db: Session, client: OpenNMSClient) -> None:
        self.db = db
        self.client = client
        self.node_repository = NodeRepository(db)
        self.alert_repository = AlertRepository(db)
        self.event_repository = EventRepository(db)
        self.outage_repository = OutageRepository(db)
        self.audit_service = AuditService(db)
        self._node_id_cache: dict[str, int] = {}

    def sync_all(self) -> IngestionRunResult:
        results = {
            "nodes": self.sync_nodes(),
            "alarms": self.sync_alarms(),
            "events": self.sync_events(),
            "outages": self.sync_outages(),
        }
        return IngestionRunResult(resources=results)

    def sync_nodes(self) -> IngestionResourceResult:
        return self._sync_resource(
            resource="nodes",
            fetcher=self.client.fetch_nodes,
            normalizer=normalize_nodes,
            writer=self._write_nodes,
        )

    def sync_alarms(self) -> IngestionResourceResult:
        return self._sync_resource(
            resource="alarms",
            fetcher=self.client.fetch_alarms,
            normalizer=normalize_alarms,
            writer=self._write_alarms,
        )

    def sync_events(self) -> IngestionResourceResult:
        return self._sync_resource(
            resource="events",
            fetcher=self.client.fetch_events,
            normalizer=normalize_events,
            writer=self._write_events,
        )

    def sync_outages(self) -> IngestionResourceResult:
        return self._sync_resource(
            resource="outages",
            fetcher=self.client.fetch_outages,
            normalizer=normalize_outages,
            writer=self._write_outages,
        )

    def _sync_resource(
        self,
        resource: str,
        fetcher: Callable,
        normalizer: Callable[[str], NormalizedBatch],
        writer: Callable[[list], int],
    ) -> IngestionResourceResult:
        errors: list[str] = []
        try:
            response = fetcher()
            batch = normalizer(response.raw_xml)
            stored_count = writer(batch.records)
            errors.extend(batch.errors)
            result = IngestionResourceResult(
                resource=resource,
                fetched_count=len(batch.records) + len(batch.errors),
                stored_count=stored_count,
                skipped_count=len(batch.errors),
                errors=errors,
            )
            self._record_audit(result)
            self.db.commit()
            return result
        except Exception as exc:
            self.db.rollback()
            logger.exception("OpenNMS ingestion failed for resource '%s'", resource)
            result = IngestionResourceResult(
                resource=resource,
                errors=[str(exc)],
            )
            self._record_audit(result)
            self.db.commit()
            return result

    def _write_nodes(self, records: list[NormalizedRecord]) -> int:
        stored_count = 0
        for record in records:
            node = self.node_repository.upsert_by_opennms_id(record.values)
            self._node_id_cache[record.opennms_id] = node.id
            stored_count += 1
        return stored_count

    def _write_alarms(self, records: list[NormalizedRelatedRecord]) -> int:
        stored_count = 0
        for record in records:
            values = dict(record.values)
            values["node_id"] = self._resolve_local_node_id(record.opennms_node_id)

            existing = self.alert_repository.get_by_opennms_alarm_id(record.opennms_id)
            previous_status = existing.lifecycle_status if existing else None
            alert = self.alert_repository.upsert_by_opennms_alarm_id(values)

            new_status = values.get("lifecycle_status", AlertLifecycleStatus.ACTIVE.value)
            if previous_status != new_status:
                self.alert_repository.add_history(
                    AlertHistory(
                        alert_id=alert.id,
                        from_status=previous_status,
                        to_status=new_status,
                        changed_by="opennms_ingestion",
                        raw_event_xml=values["raw_xml"],
                    )
                )
            stored_count += 1
        return stored_count

    def _write_events(self, records: list[NormalizedRelatedRecord]) -> int:
        stored_count = 0
        for record in records:
            values = dict(record.values)
            values["node_id"] = self._resolve_local_node_id(record.opennms_node_id)
            self.event_repository.upsert_by_opennms_event_id(values)
            stored_count += 1
        return stored_count

    def _write_outages(self, records: list[NormalizedRelatedRecord]) -> int:
        stored_count = 0
        for record in records:
            values = dict(record.values)
            values["node_id"] = self._resolve_local_node_id(record.opennms_node_id)
            self.outage_repository.upsert_by_opennms_outage_id(values)
            stored_count += 1
        return stored_count

    def _resolve_local_node_id(self, opennms_node_id: str | None) -> int | None:
        if not opennms_node_id:
            return None
        if opennms_node_id in self._node_id_cache:
            return self._node_id_cache[opennms_node_id]

        node = self.node_repository.get_by_opennms_id(opennms_node_id)
        if not node:
            return None

        self._node_id_cache[opennms_node_id] = node.id
        return node.id

    def _record_audit(self, result: IngestionResourceResult) -> None:
        self.audit_service.record(
            action="opennms_ingestion_sync",
            user_id="system",
            resource_type=result.resource,
            details={
                "resource": result.resource,
                "success": result.success,
                "fetched_count": result.fetched_count,
                "stored_count": result.stored_count,
                "skipped_count": result.skipped_count,
                "error_count": len(result.errors),
                "errors": result.errors[:10],
            },
        )
