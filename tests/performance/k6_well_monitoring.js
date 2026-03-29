/**
 * k6 Performance Test - Well Monitoring Service (Staging)
 *
 * Simulates concurrent Ignition SCADA instances polling the Well Monitoring
 * Service from multiple field sites across the Permian Basin, Eagle Ford,
 * and Williston Basin assets.
 *
 * Scenarios:
 *   1. noc_dashboard_polling  - NOC operators polling well status and alarms
 *   2. ignition_tag_push      - Ignition pushing sensor readings at scan rate
 *   3. alarm_burst            - Sudden burst of alarms (pressure event simulation)
 *
 * Thresholds (SLAs for staging gate):
 *   - 95th percentile response time < 500ms
 *   - Error rate < 1%
 *   - All health checks pass
 */
import http from "k6/http";
import { check, sleep, group } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("errors");
const readingPushDuration = new Trend("reading_push_duration");
const alarmFetchDuration = new Trend("alarm_fetch_duration");

// ── Config ─────────────────────────────────────────────────────────────────────
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

const WELLS = ["WELL-001", "WELL-002", "WELL-003", "WELL-004"];

// ── Load Profile ───────────────────────────────────────────────────────────────
export const options = {
  scenarios: {
    // NOC dashboard: steady read traffic
    noc_dashboard_polling: {
      executor: "constant-vus",
      vus: 10,
      duration: "2m",
      exec: "nocDashboard",
    },
    // Ignition tag push: simulates 4 wells × 1 push per 5 seconds
    ignition_tag_push: {
      executor: "constant-arrival-rate",
      rate: 4,
      timeUnit: "5s",
      duration: "2m",
      preAllocatedVUs: 5,
      exec: "ignitionTagPush",
    },
    // Alarm burst: simulate a pressure event hitting multiple wells simultaneously
    alarm_burst: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 0 },   // quiet period
        { duration: "15s", target: 20 },  // sudden burst
        { duration: "30s", target: 20 },  // sustained alarm flood
        { duration: "15s", target: 0 },   // resolution
      ],
      exec: "alarmBurst",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
    errors: ["rate<0.01"],
    reading_push_duration: ["p(99)<800"],
    alarm_fetch_duration: ["p(95)<300"],
  },
};

// ── Scenarios ──────────────────────────────────────────────────────────────────

export function nocDashboard() {
  group("NOC Dashboard - Well Status Overview", () => {
    // Poll all wells
    const wellsRes = http.get(`${BASE_URL}/api/v1/wells`, {
      headers: { Accept: "application/json" },
    });
    check(wellsRes, {
      "wells list 200": (r) => r.status === 200,
      "wells list has data": (r) => JSON.parse(r.body).length > 0,
    }) || errorRate.add(1);

    // Drill into a specific well
    const wellId = WELLS[Math.floor(Math.random() * WELLS.length)];

    group("Well Detail", () => {
      const wellRes = http.get(`${BASE_URL}/api/v1/wells/${wellId}`);
      check(wellRes, { "well detail 200": (r) => r.status === 200 }) ||
        errorRate.add(1);

      const alarmsRes = http.get(
        `${BASE_URL}/api/v1/wells/${wellId}/alarms?status=active`
      );
      const duration = alarmsRes.timings.duration;
      alarmFetchDuration.add(duration);
      check(alarmsRes, { "alarms 200": (r) => r.status === 200 }) ||
        errorRate.add(1);
    });
  });

  sleep(1);
}

export function ignitionTagPush() {
  const wellId = WELLS[Math.floor(Math.random() * WELLS.length)];

  // Simulate Ignition pushing a tag update (OPC-UA scan cycle)
  const reading = {
    wellhead_pressure_psi: 2000 + Math.random() * 1000,
    casing_pressure_psi: 1600 + Math.random() * 800,
    tubing_pressure_psi: 1800 + Math.random() * 900,
    flow_rate_bopd: 300 + Math.random() * 300,
    gas_oil_ratio: 700 + Math.random() * 400,
    water_cut_pct: Math.random() * 30,
    temperature_f: 130 + Math.random() * 40,
    choke_size_64th: Math.floor(16 + Math.random() * 16),
  };

  const res = http.post(
    `${BASE_URL}/api/v1/wells/${wellId}/readings`,
    JSON.stringify(reading),
    { headers: { "Content-Type": "application/json" } }
  );

  readingPushDuration.add(res.timings.duration);

  check(res, {
    "reading push 201": (r) => r.status === 201,
    "reading has timestamp": (r) => JSON.parse(r.body).timestamp !== undefined,
  }) || errorRate.add(1);
}

export function alarmBurst() {
  const wellId = WELLS[Math.floor(Math.random() * WELLS.length)];

  // Simulate Ignition raising a pressure alarm
  const alarm = {
    severity: Math.random() > 0.7 ? "critical" : "high",
    scada_tag: `[PermianBasin]${wellId}/WellheadPressure`,
    description: "Wellhead pressure exceeded high-high setpoint",
    setpoint: 4500.0,
    actual_value: 4500 + Math.random() * 1000,
    unit: "PSI",
  };

  const res = http.post(
    `${BASE_URL}/api/v1/wells/${wellId}/alarms`,
    JSON.stringify(alarm),
    { headers: { "Content-Type": "application/json" } }
  );

  check(res, {
    "alarm created 201": (r) => r.status === 201,
    "alarm is active": (r) => JSON.parse(r.body).status === "active",
  }) || errorRate.add(1);

  sleep(0.5);
}

// ── Health check (runs before scenarios) ──────────────────────────────────────
export function setup() {
  const res = http.get(`${BASE_URL}/health`);
  check(res, {
    "service is healthy": (r) => r.status === 200,
    "status is ok": (r) => JSON.parse(r.body).status === "ok",
  });
}
