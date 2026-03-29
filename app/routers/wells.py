from fastapi import APIRouter, HTTPException
from typing import List
from app.models import Well, WellCreate, WellStatus
from app import store

router = APIRouter(prefix="/api/v1/wells", tags=["Wells"])


@router.get("", response_model=List[Well])
def list_wells(status: WellStatus = None, field: str = None):
    """
    List all registered oil wells.
    Optionally filter by status or field name.
    This endpoint is polled by Ignition SCADA for the well registry.
    """
    wells = list(store.WELLS.values())
    if status:
        wells = [w for w in wells if w.status == status]
    if field:
        wells = [w for w in wells if field.lower() in w.field.lower()]
    return wells


@router.get("/{well_id}", response_model=Well)
def get_well(well_id: str):
    """Get a single well by ID."""
    well = store.WELLS.get(well_id)
    if not well:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    return well


@router.post("", response_model=Well, status_code=201)
def create_well(payload: WellCreate):
    """Register a new well in the system."""
    well_id = f"WELL-{str(len(store.WELLS) + 1).zfill(3)}"
    well = Well(
        id=well_id,
        status=WellStatus.INACTIVE,
        commissioned_date="TBD",
        **payload.model_dump(),
    )
    store.WELLS[well_id] = well
    store.READINGS[well_id] = []
    store.ALARMS[well_id] = []
    return well


@router.patch("/{well_id}/status", response_model=Well)
def update_well_status(well_id: str, status: WellStatus):
    """Update the operational status of a well."""
    well = store.WELLS.get(well_id)
    if not well:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    store.WELLS[well_id] = well.model_copy(update={"status": status})
    return store.WELLS[well_id]
