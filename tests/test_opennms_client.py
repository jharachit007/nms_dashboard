from dataclasses import dataclass

from app.connectors.opennms.client import OpenNMSClient
from app.core.config import Settings


@dataclass
class FakeResponse:
    text: str = "<nodes />"
    status_code: int = 200
    headers: dict | None = None

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.auth = None
        self.headers = {}
        self.mounted = {}
        self.calls = []

    def mount(self, prefix: str, adapter) -> None:
        self.mounted[prefix] = adapter

    def get(self, url: str, timeout: float) -> FakeResponse:
        self.calls.append((url, timeout))
        return FakeResponse(headers={"content-type": "application/xml"})


def test_opennms_client_uses_configured_auth_timeout_and_xml_accept_header() -> None:
    session = FakeSession()
    settings = Settings(
        opennms_base_url="https://opennms.example/opennms",
        opennms_username="user",
        opennms_password="secret",
        opennms_timeout_seconds=7,
    )

    client = OpenNMSClient(settings=settings, session=session)
    response = client.fetch_nodes()

    assert session.auth == ("user", "secret")
    assert session.headers["Accept"] == "application/xml"
    assert session.calls == [("https://opennms.example/opennms/rest/nodes", 7)]
    assert response.raw_xml == "<nodes />"
