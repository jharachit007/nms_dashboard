from fastapi.testclient import TestClient

from app.main import create_app


def test_static_ui_serves_login_shell() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/index.html")

    assert response.status_code == 200
    assert "OpenNMS AI NOC" in response.text
    assert "login-form" in response.text
    assert "alert-list" in response.text
