import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

HIGH_PRESSURE_ALARM = {
    "severity": "high",
    "scada_tag": "[PermianBasin]WELL-001/WellheadPressure",
    "description": "Wellhead pressure exceeded high-high setpoint",
    "setpoint": 4500.0,
    "actual_value": 4820.0,
    "unit": "PSI",
}

LOW_FLOW_ALARM = {
    "severity": "medium",
    "scada_tag": "[PermianBasin]WELL-001/FlowRate",
    "description": "Flow rate below minimum expected threshold",
    "setpoint": 100.0,
    "actual_value": 42.0,
    "unit": "BOPD",
}


class TestGetAlarms:
    def test_returns_active_alarm_for_well_004(self):
        response = client.get("/api/v1/wells/WELL-004/alarms")
        assert response.status_code == 200
        alarms = response.json()
        assert len(alarms) == 1
        assert alarms[0]["severity"] == "high"

    def test_no_alarms_for_active_well(self):
        response = client.get("/api/v1/wells/WELL-001/alarms")
        assert response.status_code == 200
        assert response.json() == []

    def test_filter_by_status(self):
        response = client.get("/api/v1/wells/WELL-004/alarms?status=active")
        assert response.status_code == 200
        alarms = response.json()
        assert all(a["status"] == "active" for a in alarms)

    def test_returns_404_for_unknown_well(self):
        response = client.get("/api/v1/wells/WELL-999/alarms")
        assert response.status_code == 404


class TestCreateAlarm:
    def test_ignition_can_trigger_alarm(self):
        response = client.post("/api/v1/wells/WELL-001/alarms", json=HIGH_PRESSURE_ALARM)
        assert response.status_code == 201
        alarm = response.json()
        assert alarm["well_id"] == "WELL-001"
        assert alarm["status"] == "active"
        assert alarm["scada_tag"] == HIGH_PRESSURE_ALARM["scada_tag"]
        assert alarm["id"].startswith("ALM-")

    def test_high_severity_alarm_escalates_well_status(self):
        client.post("/api/v1/wells/WELL-001/alarms", json=HIGH_PRESSURE_ALARM)
        well = client.get("/api/v1/wells/WELL-001").json()
        assert well["status"] == "alarm"

    def test_medium_severity_does_not_escalate_well_status(self):
        client.post("/api/v1/wells/WELL-001/alarms", json=LOW_FLOW_ALARM)
        well = client.get("/api/v1/wells/WELL-001").json()
        # medium severity should not change well status to alarm
        assert well["status"] == "active"

    def test_alarm_appears_in_get_alarms(self):
        client.post("/api/v1/wells/WELL-001/alarms", json=HIGH_PRESSURE_ALARM)
        alarms = client.get("/api/v1/wells/WELL-001/alarms").json()
        assert len(alarms) == 1


class TestAcknowledgeAlarm:
    def test_operator_can_acknowledge_alarm(self):
        alarm = client.post("/api/v1/wells/WELL-004/alarms", json=HIGH_PRESSURE_ALARM).json()
        alarm_id = alarm["id"]
        response = client.patch(
            f"/api/v1/wells/WELL-004/alarms/{alarm_id}/acknowledge",
            json={"acknowledged_by": "John Smith", "notes": "Investigating elevated pressure"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "acknowledged"

    def test_cannot_acknowledge_already_acknowledged_alarm(self):
        alarm = client.post("/api/v1/wells/WELL-004/alarms", json=HIGH_PRESSURE_ALARM).json()
        alarm_id = alarm["id"]
        client.patch(
            f"/api/v1/wells/WELL-004/alarms/{alarm_id}/acknowledge",
            json={"acknowledged_by": "John Smith"},
        )
        response = client.patch(
            f"/api/v1/wells/WELL-004/alarms/{alarm_id}/acknowledge",
            json={"acknowledged_by": "Jane Doe"},
        )
        assert response.status_code == 400


class TestResolveAlarm:
    def test_operator_can_resolve_alarm(self):
        alarm = client.post("/api/v1/wells/WELL-004/alarms", json=HIGH_PRESSURE_ALARM).json()
        alarm_id = alarm["id"]
        response = client.patch(f"/api/v1/wells/WELL-004/alarms/{alarm_id}/resolve")
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"
