"""
Health Score API Routes
Calculates and returns machine health scores and fleet status
"""

from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime
import random

router = APIRouter()

# Simulated fleet data
FLEET_MACHINES = [
    "CNC-ALPHA-921",
    "CNC-ALPHA-922",
    "CNC-BETA-101",
    "CNC-BETA-102",
    "MILL-GAMMA-301",
    "MILL-GAMMA-302",
    "LATHE-DELTA-401",
    "LATHE-DELTA-402"
]


@router.get("/health/{machine_id}")
async def get_machine_health(machine_id: str):
    """
    Get current health score and status for a machine.

    Health score is 0-100 where:
    - 90-100: Optimal condition
    - 70-89: Good condition, minor wear
    - 50-69: Moderate wear, schedule maintenance
    - 25-49: Degraded, maintenance required
    - 0-24: Critical, immediate attention
    """
    # Generate realistic health data
    health_score = generate_health_score(machine_id)

    # Determine status
    if health_score >= 90:
        status = "optimal"
        trend = "stable"
    elif health_score >= 70:
        status = "good"
        trend = "stable"
    elif health_score >= 50:
        status = "moderate"
        trend = "declining"
    elif health_score >= 25:
        status = "degraded"
        trend = "declining"
    else:
        status = "critical"
        trend = "critical"

    return {
        "machine_id": machine_id,
        "timestamp": datetime.utcnow().isoformat(),
        "health_score": health_score,
        "status": status,
        "trend": trend,
        "trend_change": round(random.uniform(-2, 1), 1),
        "components": {
            "spindle": generate_component_health("spindle"),
            "bearings": generate_component_health("bearings"),
            "drive_system": generate_component_health("drive_system"),
            "coolant_system": generate_component_health("coolant_system")
        },
        "last_maintenance": "2024-06-15T08:00:00Z",
        "next_scheduled_pm": "2024-08-15T08:00:00Z",
        "operating_hours": 4892,
        "cycles_since_overhaul": 128450
    }


@router.get("/health/{machine_id}/history")
async def get_health_history(
    machine_id: str,
    days: int = Query(default=30, le=90)
):
    """Get historical health score trend for a machine."""
    history = []
    base_health = random.randint(75, 95)

    for i in range(days):
        # Simulate gradual degradation with some noise
        daily_health = max(50, base_health - (i * 0.3) + random.uniform(-3, 3))
        history.append({
            "date": f"2024-{7 - i // 30:02d}-{(30 - i % 30):02d}",
            "health_score": round(daily_health, 1)
        })

    return {
        "machine_id": machine_id,
        "days": days,
        "history": list(reversed(history))
    }


@router.get("/health/fleet")
async def get_fleet_health():
    """
    Get health status overview for entire machine fleet.

    Used for fleet-wide monitoring dashboard.
    """
    fleet_status = []

    for machine_id in FLEET_MACHINES:
        health = generate_health_score(machine_id)
        status = "critical" if health < 25 else "degraded" if health < 50 else "moderate" if health < 70 else "good" if health < 90 else "optimal"

        fleet_status.append({
            "machine_id": machine_id,
            "health_score": health,
            "status": status,
            "location": f"Bay {FLEET_MACHINES.index(machine_id) + 1}",
            "last_alert": None if health > 70 else datetime.utcnow().isoformat()
        })

    # Sort by health score (worst first)
    fleet_status.sort(key=lambda x: x["health_score"])

    summary = {
        "total_machines": len(FLEET_MACHINES),
        "optimal": sum(1 for m in fleet_status if m["status"] == "optimal"),
        "good": sum(1 for m in fleet_status if m["status"] == "good"),
        "moderate": sum(1 for m in fleet_status if m["status"] == "moderate"),
        "degraded": sum(1 for m in fleet_status if m["status"] == "degraded"),
        "critical": sum(1 for m in fleet_status if m["status"] == "critical"),
        "average_health": round(sum(m["health_score"] for m in fleet_status) / len(fleet_status), 1)
    }

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": summary,
        "machines": fleet_status
    }


@router.get("/health/{machine_id}/anomalies")
async def get_anomaly_flags(
    machine_id: str,
    hours: int = Query(default=24, le=168)
):
    """Get recent anomaly detections for a machine."""
    anomalies = []

    # Generate synthetic anomaly events
    num_anomalies = random.randint(0, 5)
    for i in range(num_anomalies):
        severity = random.choice(["low", "medium", "high"])
        anomaly_type = random.choice([
            "vibration_spike",
            "temperature_deviation",
            "power_fluctuation",
            "pattern_anomaly"
        ])

        anomalies.append({
            "id": f"ANM-{random.randint(10000, 99999)}",
            "timestamp": f"2024-07-15T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00Z",
            "type": anomaly_type,
            "severity": severity,
            "sensor_channel": random.choice(["spindle_x", "spindle_y", "spindle_z"]),
            "value": round(random.uniform(45, 80), 2),
            "threshold": 40.0,
            "acknowledged": random.choice([True, False])
        })

    return {
        "machine_id": machine_id,
        "hours": hours,
        "count": len(anomalies),
        "anomalies": anomalies
    }


def generate_health_score(machine_id: str) -> float:
    """Generate a realistic health score based on machine ID."""
    # Use machine ID to seed consistent scores
    seed = sum(ord(c) for c in machine_id)
    random.seed(seed + int(datetime.now().hour))
    score = random.uniform(65, 98)
    random.seed()  # Reset seed
    return round(score, 1)


def generate_component_health(component: str) -> dict:
    """Generate health data for a machine component."""
    health = random.uniform(70, 99)
    return {
        "health_score": round(health, 1),
        "status": "good" if health > 80 else "fair" if health > 60 else "poor",
        "wear_indicator": round(100 - health, 1)
    }
