from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestProductionSummary:
    def test_returns_summary(self):
        response = client.get("/api/v1/summary")
        assert response.status_code == 200

    def test_total_well_count(self):
        response = client.get("/api/v1/summary")
        assert response.json()["total_wells"] == 4

    def test_by_status_breakdown(self):
        data = client.get("/api/v1/summary").json()
        assert data["by_status"]["active"] == 2
        assert data["by_status"]["maintenance"] == 1
        assert data["by_status"]["alarm"] == 1

    def test_active_alarms_count(self):
        data = client.get("/api/v1/summary").json()
        assert data["active_alarms"] == 1

    def test_total_flow_rate_is_numeric(self):
        data = client.get("/api/v1/summary").json()
        assert isinstance(data["total_flow_rate_bopd"], float)
