import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VALID_READING = {
    "wellhead_pressure_psi": 2340.5,
    "casing_pressure_psi": 1850.0,
    "tubing_pressure_psi": 2100.3,
    "flow_rate_bopd": 412.7,
    "gas_oil_ratio": 850.0,
    "water_cut_pct": 12.4,
    "temperature_f": 148.2,
    "choke_size_64th": 24,
}


class TestGetReadings:
    def test_returns_readings_for_active_well(self):
        response = client.get("/api/v1/wells/WELL-001/readings")
        assert response.status_code == 200
        readings = response.json()
        assert len(readings) >= 1

    def test_reading_has_scada_fields(self):
        response = client.get("/api/v1/wells/WELL-001/readings")
        reading = response.json()[0]
        assert "wellhead_pressure_psi" in reading
        assert "flow_rate_bopd" in reading
        assert "gas_oil_ratio" in reading
        assert "water_cut_pct" in reading
        assert "choke_size_64th" in reading

    def test_returns_404_for_unknown_well(self):
        response = client.get("/api/v1/wells/WELL-999/readings")
        assert response.status_code == 404

    def test_limit_parameter_respected(self):
        # Push several readings first
        for _ in range(5):
            client.post("/api/v1/wells/WELL-001/readings", json=VALID_READING)
        response = client.get("/api/v1/wells/WELL-001/readings?limit=3")
        assert response.status_code == 200
        assert len(response.json()) <= 3


class TestGetLatestReading:
    def test_returns_most_recent_reading(self):
        response = client.get("/api/v1/wells/WELL-001/readings/latest")
        assert response.status_code == 200
        reading = response.json()
        assert reading["well_id"] == "WELL-001"

    def test_reflects_newly_pushed_reading(self):
        new_reading = {**VALID_READING, "wellhead_pressure_psi": 9999.0}
        client.post("/api/v1/wells/WELL-001/readings", json=new_reading)
        response = client.get("/api/v1/wells/WELL-001/readings/latest")
        assert response.json()["wellhead_pressure_psi"] == 9999.0


class TestPushReading:
    def test_ignition_can_push_reading(self):
        response = client.post("/api/v1/wells/WELL-001/readings", json=VALID_READING)
        assert response.status_code == 201
        reading = response.json()
        assert reading["well_id"] == "WELL-001"
        assert reading["wellhead_pressure_psi"] == VALID_READING["wellhead_pressure_psi"]
        assert "timestamp" in reading

    def test_returns_404_for_unknown_well(self):
        response = client.post("/api/v1/wells/WELL-999/readings", json=VALID_READING)
        assert response.status_code == 404

    def test_maintenance_well_accepts_zero_flow(self):
        zero_reading = {**VALID_READING, "flow_rate_bopd": 0.0, "wellhead_pressure_psi": 0.0}
        response = client.post("/api/v1/wells/WELL-003/readings", json=zero_reading)
        assert response.status_code == 201
