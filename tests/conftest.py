import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import store
from app.models import WellStatus
import copy


@pytest.fixture(autouse=True)
def reset_store():
    """Reset in-memory store before each test to ensure isolation."""
    original_wells = copy.deepcopy(store.WELLS)
    original_readings = copy.deepcopy(store.READINGS)
    original_alarms = copy.deepcopy(store.ALARMS)
    yield
    store.WELLS = original_wells
    store.READINGS = original_readings
    store.ALARMS = original_alarms


@pytest.fixture
def client():
    return TestClient(app)
