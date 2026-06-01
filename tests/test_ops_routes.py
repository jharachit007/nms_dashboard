from fastapi.testclient import TestClient

from app.main import create_app


def test_metrics_requires_admin_role() -> None:
    client = TestClient(create_app())

    viewer = client.get("/api/v1/metrics", headers={"x-user": "viewer", "x-roles": "noc-viewer"})
    admin = client.get("/api/v1/metrics", headers={"x-user": "admin", "x-roles": "noc-admin"})

    assert viewer.status_code == 403
    assert admin.status_code == 200
    assert "metrics" in admin.json()
