from fastapi.testclient import TestClient

from app.domain.models.current_user import CurrentUser
from app.main import app
from app.di.auth import get_current_user


def _current_user() -> CurrentUser:
    return CurrentUser(
        user_id="6a3b7c61d8139334274fbbfd",
        organization_id="6a3b7c61d8139334274fbbfc",
        clerk_id="user_test",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        user_type="root",
        is_root=True,
        status="active",
        organization_name="abc bank",
        organization_industry="financial_services",
    )


def test_list_executors_endpoint() -> None:
    app.dependency_overrides[get_current_user] = _current_user
    try:
        client = TestClient(app)
        response = client.get("/api/v1/executors")
        assert response.status_code == 200
        body = response.json()
        items = body["items"]
        assert len(items) == 7
        executors = {item["executor"] for item in items}
        assert "mongo_find_one" in executors
        assert "http_request" in executors
        mongo_find_one = next(item for item in items if item["executor"] == "mongo_find_one")
        assert mongo_find_one["connector_type"] == "mongo"
        assert mongo_find_one["mvp"] is True
        assert "collection" in mongo_find_one["config_schema"]
    finally:
        app.dependency_overrides.clear()
