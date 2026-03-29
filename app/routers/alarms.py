from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, UTC
from app.models import Alarm, AlarmCreate, AlarmAcknowledge, AlarmStatus, WellStatus
from app import store

router = APIRouter(prefix="/api/v1/wells", tags=["Alarms"])


@router.get("/{well_id}/alarms", response_model=List[Alarm])
def get_alarms(well_id: str, status: AlarmStatus = None):
    """
    Retrieve alarms for a well.
    Ignition alarm journal writes to this endpoint; the NOC dashboard reads from it.
    """
    if well_id not in store.WELLS:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    alarms = store.ALARMS.get(well_id, [])
    if status:
        alarms = [a for a in alarms if a.status == status]
    return alarms


@router.post("/{well_id}/alarms", response_model=Alarm, status_code=201)
def create_alarm(well_id: str, payload: AlarmCreate):
    """
    Trigger a new alarm from an Ignition SCADA tag event.
    Ignition calls this when a tag value breaches a configured setpoint.
    """
    if well_id not in store.WELLS:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")

    alarm_id = f"ALM-{datetime.now(UTC).strftime('%Y%m%d')}-{str(len(store.ALARMS[well_id]) + 1).zfill(3)}"
    alarm = Alarm(
        id=alarm_id,
        well_id=well_id,
        timestamp=datetime.now(UTC),
        status=AlarmStatus.ACTIVE,
        **payload.model_dump(),
    )
    store.ALARMS[well_id].append(alarm)

    # Escalate well status to ALARM if severity is HIGH or CRITICAL
    if payload.severity.value in ("high", "critical"):
        well = store.WELLS[well_id]
        store.WELLS[well_id] = well.model_copy(update={"status": WellStatus.ALARM})

    return alarm


@router.patch("/{well_id}/alarms/{alarm_id}/acknowledge", response_model=Alarm)
def acknowledge_alarm(well_id: str, alarm_id: str, payload: AlarmAcknowledge):
    """Acknowledge an active alarm (NOC operator action)."""
    if well_id not in store.WELLS:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    alarms = store.ALARMS.get(well_id, [])
    for i, alarm in enumerate(alarms):
        if alarm.id == alarm_id:
            if alarm.status != AlarmStatus.ACTIVE:
                raise HTTPException(status_code=400, detail="Only ACTIVE alarms can be acknowledged")
            store.ALARMS[well_id][i] = alarm.model_copy(update={"status": AlarmStatus.ACKNOWLEDGED})
            return store.ALARMS[well_id][i]
    raise HTTPException(status_code=404, detail=f"Alarm '{alarm_id}' not found")


@router.patch("/{well_id}/alarms/{alarm_id}/resolve", response_model=Alarm)
def resolve_alarm(well_id: str, alarm_id: str):
    """Mark an alarm as resolved."""
    if well_id not in store.WELLS:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    alarms = store.ALARMS.get(well_id, [])
    for i, alarm in enumerate(alarms):
        if alarm.id == alarm_id:
            store.ALARMS[well_id][i] = alarm.model_copy(update={"status": AlarmStatus.RESOLVED})
            return store.ALARMS[well_id][i]
    raise HTTPException(status_code=404, detail=f"Alarm '{alarm_id}' not found")
