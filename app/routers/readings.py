from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, UTC
from app.models import SensorReading, SensorReadingCreate
from app import store

router = APIRouter(prefix="/api/v1/wells", tags=["Readings"])


@router.get("/{well_id}/readings", response_model=List[SensorReading])
def get_readings(well_id: str, limit: int = 10):
    """
    Retrieve the latest sensor readings for a well.
    Called by Ignition SCADA on a configurable poll interval (typically 5s-1min).
    Data flows: RTU/PLC → OPC-UA Server → Ignition → this endpoint.
    """
    if well_id not in store.WELLS:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    readings = store.READINGS.get(well_id, [])
    return readings[-limit:]


@router.get("/{well_id}/readings/latest", response_model=SensorReading)
def get_latest_reading(well_id: str):
    """Get the most recent sensor reading for a well."""
    if well_id not in store.WELLS:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    readings = store.READINGS.get(well_id, [])
    if not readings:
        raise HTTPException(status_code=404, detail=f"No readings found for well '{well_id}'")
    return readings[-1]


@router.post("/{well_id}/readings", response_model=SensorReading, status_code=201)
def push_reading(well_id: str, payload: SensorReadingCreate):
    """
    Push a new sensor reading from Ignition SCADA.
    Ignition calls this endpoint when tag values are updated from field devices.
    """
    if well_id not in store.WELLS:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    reading = SensorReading(
        well_id=well_id,
        timestamp=datetime.now(UTC),
        **payload.model_dump(),
    )
    store.READINGS[well_id].append(reading)
    return reading
