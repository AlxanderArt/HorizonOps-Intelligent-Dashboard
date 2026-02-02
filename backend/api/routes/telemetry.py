"""
Telemetry API Routes
Handles real-time sensor data ingestion and streaming
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio
import json
import random

router = APIRouter()

# Simulated telemetry storage (would be Redis/TimescaleDB in production)
telemetry_buffer = {}


@router.get("/telemetry/{machine_id}")
async def get_telemetry(
    machine_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """
    Retrieve historical telemetry data for a machine.

    Parameters:
    - machine_id: Target machine identifier
    - start_time: ISO timestamp for range start
    - end_time: ISO timestamp for range end
    - limit: Maximum records to return
    """
    # Generate synthetic historical data
    data = generate_synthetic_telemetry(machine_id, limit)

    return {
        "machine_id": machine_id,
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(data),
        "data": data
    }


@router.get("/telemetry/{machine_id}/latest")
async def get_latest_telemetry(machine_id: str):
    """Get the most recent telemetry reading for a machine."""
    reading = generate_single_reading(machine_id)

    return {
        "machine_id": machine_id,
        "timestamp": datetime.utcnow().isoformat(),
        "reading": reading
    }


@router.websocket("/telemetry/{machine_id}/stream")
async def telemetry_stream(websocket: WebSocket, machine_id: str):
    """
    WebSocket endpoint for real-time telemetry streaming.

    Streams sensor data at ~1Hz for live dashboard updates.
    """
    await websocket.accept()

    try:
        while True:
            # Generate real-time reading
            reading = generate_single_reading(machine_id)

            await websocket.send_json({
                "machine_id": machine_id,
                "timestamp": datetime.utcnow().isoformat(),
                "reading": reading
            })

            await asyncio.sleep(1)  # 1Hz update rate

    except WebSocketDisconnect:
        pass


@router.post("/telemetry/ingest")
async def ingest_telemetry(data: dict):
    """
    Ingest telemetry data point from sensor gateway.

    Expected format:
    {
        "machine_id": "CNC-ALPHA-921",
        "sensor_type": "vibration",
        "channel": "spindle_x",
        "value": 22.4,
        "timestamp": "2024-07-15T14:32:00.000Z"
    }
    """
    machine_id = data.get("machine_id")
    if not machine_id:
        return {"status": "error", "message": "machine_id required"}

    # Store in buffer (would write to time-series DB)
    if machine_id not in telemetry_buffer:
        telemetry_buffer[machine_id] = []

    telemetry_buffer[machine_id].append({
        **data,
        "ingested_at": datetime.utcnow().isoformat()
    })

    # Keep buffer bounded
    if len(telemetry_buffer[machine_id]) > 10000:
        telemetry_buffer[machine_id] = telemetry_buffer[machine_id][-5000:]

    return {
        "status": "accepted",
        "machine_id": machine_id,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/telemetry/{machine_id}/statistics")
async def get_telemetry_statistics(
    machine_id: str,
    window_minutes: int = Query(default=60, le=1440)
):
    """
    Get aggregated statistics for telemetry over a time window.

    Returns min, max, mean, std for each sensor channel.
    """
    # Generate synthetic statistics
    return {
        "machine_id": machine_id,
        "window_minutes": window_minutes,
        "timestamp": datetime.utcnow().isoformat(),
        "statistics": {
            "vibration": {
                "rms": {"min": 18.2, "max": 28.4, "mean": 22.1, "std": 2.3},
                "peak": {"min": 32.1, "max": 52.8, "mean": 41.2, "std": 4.8},
                "kurtosis": {"min": 2.8, "max": 4.2, "mean": 3.4, "std": 0.3}
            },
            "temperature": {
                "spindle": {"min": 41.2, "max": 48.9, "mean": 44.8, "std": 1.9},
                "ambient": {"min": 22.1, "max": 24.8, "mean": 23.2, "std": 0.6}
            },
            "power": {
                "consumption": {"min": 10.8, "max": 13.2, "mean": 11.9, "std": 0.5},
                "deviation": {"min": -3.2, "max": 4.8, "mean": 0.2, "std": 1.8}
            }
        }
    }


def generate_synthetic_telemetry(machine_id: str, count: int) -> List[dict]:
    """Generate synthetic telemetry data for demonstration."""
    data = []
    base_time = datetime.utcnow()

    for i in range(count):
        timestamp = base_time - timedelta(seconds=i * 3)
        is_anomaly = random.random() > 0.98

        data.append({
            "timestamp": timestamp.isoformat(),
            "vibration_rms": 55 + random.uniform(-10, 25) if is_anomaly else 20 + random.uniform(-2, 4),
            "vibration_peak": 80 + random.uniform(0, 30) if is_anomaly else 35 + random.uniform(-5, 10),
            "vibration_kurtosis": 6 + random.uniform(0, 3) if is_anomaly else 3.2 + random.uniform(-0.3, 0.5),
            "temperature": 44 + random.uniform(-2, 3),
            "power_consumption": 12 + random.uniform(-0.5, 0.5),
            "anomaly_flag": is_anomaly
        })

    return list(reversed(data))


def generate_single_reading(machine_id: str) -> dict:
    """Generate a single real-time telemetry reading."""
    is_anomaly = random.random() > 0.98

    return {
        "vibration_rms": 55 + random.uniform(-10, 25) if is_anomaly else 20 + random.uniform(-2, 4),
        "vibration_peak": 80 + random.uniform(0, 30) if is_anomaly else 35 + random.uniform(-5, 10),
        "vibration_kurtosis": 6 + random.uniform(0, 3) if is_anomaly else 3.2 + random.uniform(-0.3, 0.5),
        "temperature": 44 + random.uniform(-2, 3),
        "power_consumption": 12 + random.uniform(-0.5, 0.5),
        "anomaly_flag": is_anomaly,
        "quality_flag": "valid"
    }
