import logging
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import Settings

logger = logging.getLogger(__name__)


class OpenNMSConnectorError(Exception):
    """Base error for OpenNMS connector failures."""


class OpenNMSConfigurationError(OpenNMSConnectorError):
    """Raised when OpenNMS connector settings are incomplete."""


class OpenNMSRequestError(OpenNMSConnectorError):
    """Raised when an OpenNMS HTTP request fails."""


@dataclass(frozen=True)
class OpenNMSXMLResponse:
    resource: str
    url: str
    status_code: int
    raw_xml: str


class OpenNMSClient:
    RESOURCE_PATHS = {
        "nodes": "rest/nodes",
        "alarms": "rest/alarms",
        "events": "rest/events",
        "outages": "rest/outages",
    }

    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        if not settings.opennms_base_url:
            raise OpenNMSConfigurationError("opennms_base_url is required")
        if not settings.opennms_username or not settings.opennms_password:
            raise OpenNMSConfigurationError("OpenNMS username and password are required")

        self.base_url = settings.opennms_base_url.rstrip("/") + "/"
        self.timeout_seconds = settings.opennms_timeout_seconds
        self.session = session or requests.Session()
        self.session.auth = (settings.opennms_username, settings.opennms_password)
        self.session.headers.update({"Accept": "application/xml"})

        retries = Retry(
            total=settings.opennms_max_retries,
            connect=settings.opennms_max_retries,
            read=settings.opennms_max_retries,
            status=settings.opennms_max_retries,
            backoff_factor=settings.opennms_backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch_nodes(self) -> OpenNMSXMLResponse:
        return self.fetch_resource("nodes")

    def fetch_alarms(self) -> OpenNMSXMLResponse:
        return self.fetch_resource("alarms")

    def fetch_events(self) -> OpenNMSXMLResponse:
        return self.fetch_resource("events")

    def fetch_outages(self) -> OpenNMSXMLResponse:
        return self.fetch_resource("outages")

    def fetch_resource(self, resource: str) -> OpenNMSXMLResponse:
        if resource not in self.RESOURCE_PATHS:
            raise OpenNMSConfigurationError(f"unsupported OpenNMS resource: {resource}")

        url = urljoin(self.base_url, self.RESOURCE_PATHS[resource])
        logger.info("Fetching OpenNMS resource '%s' from %s", resource, url)
        try:
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OpenNMSRequestError(f"failed to fetch OpenNMS resource '{resource}'") from exc

        content_type = response.headers.get("content-type", "")
        if "xml" not in content_type.lower():
            logger.warning(
                "OpenNMS resource '%s' returned non-XML content type '%s'",
                resource,
                content_type,
            )

        return OpenNMSXMLResponse(
            resource=resource,
            url=url,
            status_code=response.status_code,
            raw_xml=response.text,
        )
