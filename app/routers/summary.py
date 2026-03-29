from fastapi import APIRouter
from app import store
from app.models import WellStatus

router = APIRouter(prefix="/api/v1/summary", tags=["Summary"])


@router.get("")
def get_production_summary():
    """
    Returns a high-level production summary across all wells.
    Used by the NOC dashboard header and daily operations report.
    """
    wells = list(store.WELLS.values())

    total_flow = sum(
        r[-1].flow_rate_bopd
        for w in wells
        if store.READINGS.get(w.id)
        for r in [store.READINGS[w.id]]
        if r
    )

    return {
        "total_wells": len(wells),
        "by_status": {
            status.value: sum(1 for w in wells if w.status == status)
            for status in WellStatus
        },
        "total_flow_rate_bopd": round(total_flow, 1),
        "active_alarms": sum(
            len([a for a in store.ALARMS.get(w.id, []) if a.status.value == "active"])
            for w in wells
        ),
    }
