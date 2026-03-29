"""
Pact Provider Verification - WellMonitoringService

This test verifies that the WellMonitoringService fulfils the contracts
published by its consumer: SCADA-Ignition.

In a full Pact setup, pacts would be fetched from a Pact Broker.
For this demo, we read the pact file directly from the repository.

Consumer:  SCADA-Ignition (Inductive Automation Ignition SCADA platform)
Provider:  WellMonitoringService (this service)

How this fits in the pipeline:
  - The Ignition team owns and publishes the pact (consumer-driven)
  - This verification runs in the WellMonitoringService CI pipeline
  - A failed verification blocks deployment - the provider cannot break its consumers
"""
import pytest
import json
import os
from fastapi.testclient import TestClient
from app.main import app
from app import store

client = TestClient(app)

PACT_FILE = os.path.join(
    os.path.dirname(__file__),
    "pacts",
    "scada-ignition-wellmonitoringservice.json",
)


def load_pact() -> dict:
    with open(PACT_FILE) as f:
        return json.load(f)


def apply_provider_state(state: str):
    """
    Set up the provider state described in the pact interaction.
    In a real Pact setup this would be handled by a provider state endpoint.
    """
    pass  # Our in-memory store already seeds the required state


class TestPactProviderVerification:
    """
    Manually walks each pact interaction and verifies the provider response
    matches the contract expectations.
    """

    def setup_method(self):
        self.pact = load_pact()
        self.interactions = self.pact["interactions"]

    def _find_interaction(self, description: str) -> dict:
        for interaction in self.interactions:
            if interaction["description"] == description:
                return interaction
        raise ValueError(f"Interaction not found: {description}")

    def test_pact_consumer_and_provider_names(self):
        assert self.pact["consumer"]["name"] == "SCADA-Ignition"
        assert self.pact["provider"]["name"] == "WellMonitoringService"

    def test_list_active_wells(self):
        interaction = self._find_interaction("a request for all active wells")
        apply_provider_state(interaction["providerState"])

        response = client.get("/api/v1/wells?status=active")

        assert response.status_code == interaction["response"]["status"]
        body = response.json()
        assert isinstance(body, list)
        assert len(body) >= 1

        # Verify response shape matches pact contract
        for well in body:
            assert "id" in well
            assert "name" in well
            assert "status" in well
            assert well["status"] == "active"
            assert "api_number" in well
            assert isinstance(well["depth_ft"], float)

    def test_get_latest_reading(self):
        interaction = self._find_interaction(
            "a request for the latest sensor reading of a well"
        )
        apply_provider_state(interaction["providerState"])

        response = client.get("/api/v1/wells/WELL-001/readings/latest")

        assert response.status_code == interaction["response"]["status"]
        body = response.json()

        # Verify all SCADA-expected fields are present and correct types
        assert isinstance(body["well_id"], str)
        assert isinstance(body["wellhead_pressure_psi"], float)
        assert isinstance(body["casing_pressure_psi"], float)
        assert isinstance(body["tubing_pressure_psi"], float)
        assert isinstance(body["flow_rate_bopd"], float)
        assert isinstance(body["gas_oil_ratio"], float)
        assert isinstance(body["water_cut_pct"], float)
        assert isinstance(body["temperature_f"], float)
        assert isinstance(body["choke_size_64th"], int)
        assert "timestamp" in body

    def test_push_sensor_reading(self):
        interaction = self._find_interaction("Ignition pushes a new sensor reading")
        apply_provider_state(interaction["providerState"])

        payload = interaction["request"]["body"]
        response = client.post("/api/v1/wells/WELL-001/readings", json=payload)

        assert response.status_code == interaction["response"]["status"]
        body = response.json()
        assert body["well_id"] == "WELL-001"
        assert isinstance(body["wellhead_pressure_psi"], float)
        assert "timestamp" in body

    def test_trigger_alarm(self):
        interaction = self._find_interaction("Ignition triggers a high-pressure alarm")
        apply_provider_state(interaction["providerState"])

        payload = interaction["request"]["body"]
        response = client.post("/api/v1/wells/WELL-001/alarms", json=payload)

        assert response.status_code == interaction["response"]["status"]
        body = response.json()
        assert body["well_id"] == "WELL-001"
        assert body["severity"] == "high"
        assert body["status"] == "active"
        assert body["scada_tag"] == payload["scada_tag"]
        assert body["id"].startswith("ALM-")

    def test_get_active_alarms(self):
        interaction = self._find_interaction(
            "a request for active alarms on a well"
        )
        apply_provider_state(interaction["providerState"])

        response = client.get("/api/v1/wells/WELL-004/alarms?status=active")

        assert response.status_code == interaction["response"]["status"]
        body = response.json()
        assert isinstance(body, list)
        assert len(body) >= 1

        alarm = body[0]
        assert "id" in alarm
        assert "well_id" in alarm
        assert "severity" in alarm
        assert alarm["status"] == "active"
        assert "scada_tag" in alarm
        assert isinstance(alarm["setpoint"], float)
        assert isinstance(alarm["actual_value"], float)
