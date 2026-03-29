"""
In-memory data store - simulates a time-series historian + well registry.
In production this would be backed by an OSIsoft PI / InfluxDB historian
and a relational well registry (Postgres/SQL Server).
"""
from datetime import datetime
from app.models import Well, WellStatus, SensorReading, Alarm, AlarmSeverity, AlarmStatus

# ── Well Registry ──────────────────────────────────────────────────────────────
WELLS: dict[str, Well] = {
    "WELL-001": Well(
        id="WELL-001",
        name="Permian Alpha-1",
        field="Permian Basin",
        location="32.7767° N, 102.3978° W",
        operator="Fuel Energy Corp",
        api_number="42-317-20130",
        depth_ft=9450.0,
        status=WellStatus.ACTIVE,
        commissioned_date="2019-03-15",
    ),
    "WELL-002": Well(
        id="WELL-002",
        name="Permian Alpha-2",
        field="Permian Basin",
        location="32.7812° N, 102.4021° W",
        operator="Fuel Energy Corp",
        api_number="42-317-20131",
        depth_ft=9800.0,
        status=WellStatus.ACTIVE,
        commissioned_date="2019-06-22",
    ),
    "WELL-003": Well(
        id="WELL-003",
        name="Eagle Ford Beta-1",
        field="Eagle Ford Shale",
        location="28.5383° N, 99.1699° W",
        operator="Fuel Energy Corp",
        api_number="42-131-31045",
        depth_ft=7200.0,
        status=WellStatus.MAINTENANCE,
        commissioned_date="2021-11-08",
    ),
    "WELL-004": Well(
        id="WELL-004",
        name="Bakken Delta-3",
        field="Williston Basin",
        location="47.8535° N, 103.6215° W",
        operator="Fuel Energy Corp",
        api_number="33-053-04712",
        depth_ft=11200.0,
        status=WellStatus.ALARM,
        commissioned_date="2020-07-30",
    ),
}

# ── Sensor Readings (latest per well) ─────────────────────────────────────────
READINGS: dict[str, list[SensorReading]] = {
    "WELL-001": [
        SensorReading(
            well_id="WELL-001",
            timestamp=datetime(2026, 3, 29, 6, 0, 0),
            wellhead_pressure_psi=2340.5,
            casing_pressure_psi=1850.0,
            tubing_pressure_psi=2100.3,
            flow_rate_bopd=412.7,
            gas_oil_ratio=850.0,
            water_cut_pct=12.4,
            temperature_f=148.2,
            choke_size_64th=24,
        )
    ],
    "WELL-002": [
        SensorReading(
            well_id="WELL-002",
            timestamp=datetime(2026, 3, 29, 6, 0, 0),
            wellhead_pressure_psi=2180.0,
            casing_pressure_psi=1720.5,
            tubing_pressure_psi=1950.8,
            flow_rate_bopd=388.1,
            gas_oil_ratio=790.0,
            water_cut_pct=18.9,
            temperature_f=142.7,
            choke_size_64th=22,
        )
    ],
    "WELL-003": [
        SensorReading(
            well_id="WELL-003",
            timestamp=datetime(2026, 3, 28, 14, 30, 0),
            wellhead_pressure_psi=0.0,
            casing_pressure_psi=0.0,
            tubing_pressure_psi=0.0,
            flow_rate_bopd=0.0,
            gas_oil_ratio=0.0,
            water_cut_pct=0.0,
            temperature_f=72.0,
            choke_size_64th=0,
        )
    ],
    "WELL-004": [
        SensorReading(
            well_id="WELL-004",
            timestamp=datetime(2026, 3, 29, 5, 45, 0),
            wellhead_pressure_psi=4820.0,
            casing_pressure_psi=4100.0,
            tubing_pressure_psi=4600.5,
            flow_rate_bopd=620.3,
            gas_oil_ratio=1240.0,
            water_cut_pct=8.1,
            temperature_f=162.4,
            choke_size_64th=28,
        )
    ],
}

# ── Alarms ─────────────────────────────────────────────────────────────────────
ALARMS: dict[str, list[Alarm]] = {
    "WELL-001": [],
    "WELL-002": [],
    "WELL-003": [],
    "WELL-004": [
        Alarm(
            id="ALM-20260329-001",
            well_id="WELL-004",
            timestamp=datetime(2026, 3, 29, 5, 47, 12),
            severity=AlarmSeverity.HIGH,
            status=AlarmStatus.ACTIVE,
            scada_tag="[WillistonBasin]WELL-004/WellheadPressure",
            description="Wellhead pressure exceeded high-high setpoint",
            setpoint=4500.0,
            actual_value=4820.0,
            unit="PSI",
        )
    ],
}

_alarm_counter = 2
