from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import wells, readings, alarms
from app.models import HealthResponse

app = FastAPI(
    title="Well Monitoring Service",
    description=(
        "REST API for oil well telemetry, production data, and alarm management. "
        "Designed to integrate with Ignition SCADA via OPC-UA tag subscriptions and "
        "REST-based historian writes. Consumed by NOC dashboards and production engineering tools."
    ),
    version="1.0.0",
    contact={
        "name": "Fuel Energy Corp - Platform Engineering",
    },
    license_info={"name": "Proprietary"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wells.router)
app.include_router(readings.router)
app.include_router(alarms.router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        service="well-monitoring-service",
    )
