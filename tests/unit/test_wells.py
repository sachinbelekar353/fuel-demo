import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestListWells:
    def test_returns_all_wells(self):
        response = client.get("/api/v1/wells")
        assert response.status_code == 200
        wells = response.json()
        assert len(wells) == 4

    def test_filter_by_status_active(self):
        response = client.get("/api/v1/wells?status=active")
        assert response.status_code == 200
        wells = response.json()
        assert all(w["status"] == "active" for w in wells)
        assert len(wells) == 2

    def test_filter_by_field(self):
        response = client.get("/api/v1/wells?field=Permian")
        assert response.status_code == 200
        wells = response.json()
        assert len(wells) == 2
        assert all("Permian" in w["field"] for w in wells)

    def test_well_has_required_fields(self):
        response = client.get("/api/v1/wells")
        well = response.json()[0]
        assert "id" in well
        assert "name" in well
        assert "api_number" in well
        assert "depth_ft" in well
        assert "status" in well


class TestGetWell:
    def test_returns_well_by_id(self):
        response = client.get("/api/v1/wells/WELL-001")
        assert response.status_code == 200
        well = response.json()
        assert well["id"] == "WELL-001"
        assert well["name"] == "Permian Alpha-1"

    def test_returns_404_for_unknown_well(self):
        response = client.get("/api/v1/wells/WELL-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_bakken_well_in_alarm_status(self):
        response = client.get("/api/v1/wells/WELL-004")
        assert response.status_code == 200
        assert response.json()["status"] == "alarm"


class TestCreateWell:
    def test_creates_new_well(self):
        payload = {
            "name": "Haynesville Gamma-1",
            "field": "Haynesville Shale",
            "location": "32.1° N, 93.6° W",
            "operator": "Fuel Energy Corp",
            "api_number": "17-017-22001",
            "depth_ft": 12500.0,
        }
        response = client.post("/api/v1/wells", json=payload)
        assert response.status_code == 201
        well = response.json()
        assert well["name"] == "Haynesville Gamma-1"
        assert well["status"] == "inactive"
        assert well["id"].startswith("WELL-")

    def test_newly_created_well_is_retrievable(self):
        payload = {
            "name": "Test Well",
            "field": "Test Field",
            "location": "0.0, 0.0",
            "operator": "Test Corp",
            "api_number": "00-000-00001",
            "depth_ft": 5000.0,
        }
        created = client.post("/api/v1/wells", json=payload).json()
        response = client.get(f"/api/v1/wells/{created['id']}")
        assert response.status_code == 200


class TestUpdateWellStatus:
    def test_update_status_to_maintenance(self):
        response = client.patch("/api/v1/wells/WELL-001/status?status=maintenance")
        assert response.status_code == 200
        assert response.json()["status"] == "maintenance"

    def test_update_status_reflects_in_get(self):
        client.patch("/api/v1/wells/WELL-002/status?status=inactive")
        response = client.get("/api/v1/wells/WELL-002")
        assert response.json()["status"] == "inactive"
