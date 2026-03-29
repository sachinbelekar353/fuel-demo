from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class WellStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ALARM = "alarm"


class Well(BaseModel):
    id: str
    name: str
    field: str
    location: str
    operator: str
    api_number: str
    depth_ft: float
    status: WellStatus
    commissioned_date: str


class WellCreate(BaseModel):
    name: str
    field: str
    location: str
    operator: str
    api_number: str
    depth_ft: float


class SensorReading(BaseModel):
    well_id: str
    timestamp: datetime
    # Pressure readings (PSI) - from Ignition OPC-UA tags
    wellhead_pressure_psi: float = Field(..., description="Wellhead tubing pressure in PSI")
    casing_pressure_psi: float = Field(..., description="Annular casing pressure in PSI")
    tubing_pressure_psi: float = Field(..., description="Tubing head pressure in PSI")
    # Production metrics
    flow_rate_bopd: float = Field(..., description="Oil flow rate in barrels per day")
    gas_oil_ratio: float = Field(..., description="Gas-oil ratio in SCF/BBL")
    water_cut_pct: float = Field(..., description="Water cut percentage 0-100")
    # Environmental
    temperature_f: float = Field(..., description="Wellhead temperature in Fahrenheit")
    choke_size_64th: int = Field(..., description="Choke size in 64ths of an inch")


class SensorReadingCreate(BaseModel):
    wellhead_pressure_psi: float
    casing_pressure_psi: float
    tubing_pressure_psi: float
    flow_rate_bopd: float
    gas_oil_ratio: float
    water_cut_pct: float
    temperature_f: float
    choke_size_64th: int


class AlarmSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlarmStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alarm(BaseModel):
    id: str
    well_id: str
    timestamp: datetime
    severity: AlarmSeverity
    status: AlarmStatus
    scada_tag: str = Field(..., description="Ignition SCADA tag path that triggered the alarm")
    description: str
    setpoint: float
    actual_value: float
    unit: str


class AlarmCreate(BaseModel):
    severity: AlarmSeverity
    scada_tag: str
    description: str
    setpoint: float
    actual_value: float
    unit: str


class AlarmAcknowledge(BaseModel):
    acknowledged_by: str
    notes: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str
