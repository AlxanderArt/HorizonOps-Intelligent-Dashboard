# AegisOps API Specification

## Base URL

```
Production: https://api.aegisops.internal/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <jwt_token>
```

---

## Prediction Endpoints

### POST /predict

Generate failure prediction for a single machine.

**Request:**
```json
{
  "machine_id": "CNC-ALPHA-921",
  "features": {
    "vibration_rms": 22.5,
    "vibration_peak": 38.2,
    "vibration_kurtosis": 3.4,
    "temperature": 45.0,
    "temp_rate_of_change": 0.1,
    "power_consumption": 12.1,
    "power_deviation": 1.5,
    "time_since_maintenance": 200,
    "cumulative_cycles": 120000
  },
  "request_explanation": true
}
```

**Response:**
```json
{
  "prediction_id": "pred_abc123",
  "machine_id": "CNC-ALPHA-921",
  "timestamp": "2024-07-15T14:32:00Z",
  "risk_score": 34.2,
  "failure_probability": 0.291,
  "risk_level": "medium",
  "recommended_action": "Increase monitoring frequency. Schedule inspection within 7 days.",
  "confidence": 0.87,
  "explanation": {
    "feature_contributions": {
      "vibration_kurtosis": 8.2,
      "vibration_rms": 6.1,
      "temperature": 4.5,
      "time_since_maintenance": 12.3,
      "power_deviation": 3.1
    },
    "top_factors": [
      {"feature": "time_since_maintenance", "contribution": 12.3},
      {"feature": "vibration_kurtosis", "contribution": 8.2},
      {"feature": "vibration_rms", "contribution": 6.1}
    ],
    "natural_language": "Extended time since last PM (200 hours) increases probability of undetected wear accumulation."
  }
}
```

### POST /predict/batch

Batch prediction for multiple machines.

**Request:**
```json
{
  "machines": [
    {"machine_id": "CNC-ALPHA-921", "features": {...}},
    {"machine_id": "CNC-ALPHA-922", "features": {...}}
  ]
}
```

---

## Health Endpoints

### GET /health/{machine_id}

Get current health score for a machine.

**Response:**
```json
{
  "machine_id": "CNC-ALPHA-921",
  "timestamp": "2024-07-15T14:32:00Z",
  "health_score": 87.3,
  "status": "good",
  "trend": "stable",
  "trend_change": -0.5,
  "components": {
    "spindle": {"health_score": 92.1, "status": "good"},
    "bearings": {"health_score": 78.4, "status": "fair"},
    "drive_system": {"health_score": 95.2, "status": "good"}
  },
  "last_maintenance": "2024-06-15T08:00:00Z",
  "next_scheduled_pm": "2024-08-15T08:00:00Z"
}
```

### GET /health/fleet

Get health overview for all machines.

**Response:**
```json
{
  "timestamp": "2024-07-15T14:32:00Z",
  "summary": {
    "total_machines": 8,
    "optimal": 3,
    "good": 3,
    "moderate": 1,
    "degraded": 1,
    "critical": 0,
    "average_health": 82.4
  },
  "machines": [
    {"machine_id": "CNC-ALPHA-921", "health_score": 87.3, "status": "good"},
    ...
  ]
}
```

---

## Telemetry Endpoints

### GET /telemetry/{machine_id}

Get historical telemetry data.

**Query Parameters:**
- `start_time` (optional): ISO timestamp
- `end_time` (optional): ISO timestamp
- `limit` (optional): Max records (default: 100, max: 1000)

### GET /telemetry/{machine_id}/latest

Get most recent telemetry reading.

### WebSocket /telemetry/{machine_id}/stream

Real-time telemetry stream (1Hz).

**Message Format:**
```json
{
  "machine_id": "CNC-ALPHA-921",
  "timestamp": "2024-07-15T14:32:01Z",
  "reading": {
    "vibration_rms": 21.3,
    "vibration_peak": 36.8,
    "temperature": 44.2,
    "power_consumption": 12.0
  }
}
```

---

## Feedback Endpoints

### POST /feedback

Submit feedback on a prediction.

**Request:**
```json
{
  "prediction_id": "pred_abc123",
  "machine_id": "CNC-ALPHA-921",
  "actual_outcome": "failure",
  "was_prediction_accurate": true,
  "user_notes": "Bearing replaced as predicted",
  "action_taken": "preventive_maintenance",
  "time_to_event": 48.5
}
```

### GET /feedback/statistics

Get aggregated feedback statistics.

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "INVALID_FEATURE",
    "message": "vibration_rms must be positive",
    "details": {
      "field": "vibration_rms",
      "value": -5.0,
      "constraint": "positive"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_FEATURE` | 400 | Feature value out of range |
| `MACHINE_NOT_FOUND` | 404 | Unknown machine_id |
| `MODEL_ERROR` | 500 | Model inference failed |
| `FEATURE_STALE` | 422 | Feature data too old |
| `RATE_LIMITED` | 429 | Too many requests |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| /predict | 100 req/min |
| /predict/batch | 10 req/min |
| /telemetry | 1000 req/min |
| /health | 500 req/min |
