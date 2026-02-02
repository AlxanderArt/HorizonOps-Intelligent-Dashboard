# AegisOps System Architecture

## Overview

AegisOps is designed as a modular, scalable system for real-time predictive maintenance in aerospace manufacturing environments. The architecture prioritizes:

- **Low Latency**: Sub-second prediction response times
- **Reliability**: Graceful degradation with fallback mechanisms
- **Explainability**: Every prediction includes human-readable explanations
- **Auditability**: Complete logging for compliance requirements

## System Components

### 1. Data Ingestion Layer

```
┌─────────────────────────────────────────────────────────────┐
│                    SENSOR GATEWAY                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Vibration│  │  Temp    │  │  Power   │  │  SCADA   │    │
│  │ Sensors  │  │ Probes   │  │  Meters  │  │  PLC     │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
│       └─────────────┴─────────────┴─────────────┘           │
│                           │                                 │
│                    ┌──────▼──────┐                          │
│                    │   Kafka     │                          │
│                    │   Topics    │                          │
│                    └──────┬──────┘                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
```

**Components:**
- **Sensor Gateway**: OPC-UA/MQTT bridge for industrial protocols
- **Kafka Topics**: Partitioned by machine_id for ordered processing
- **Schema Registry**: Avro schemas for data validation

### 2. Feature Engineering Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                  FEATURE STORE                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Raw       │    │   Window    │    │   Feature   │     │
│  │   Buffer    │───▶│   Compute   │───▶│   Cache     │     │
│  │   (Redis)   │    │   (Python)  │    │   (Redis)   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
│  Features Computed:                                         │
│  • vibration_rms (5min, 1hr rolling)                       │
│  • vibration_kurtosis (1hr rolling)                        │
│  • temperature_mean, rate_of_change                        │
│  • power_deviation from baseline                           │
│  • time_since_maintenance                                  │
│  • cumulative_cycles                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Design Decisions:**
- Rolling windows computed incrementally (not batch)
- Feature values cached with TTL for low-latency serving
- Backfill capability for model retraining

### 3. ML Serving Layer

```
┌─────────────────────────────────────────────────────────────┐
│                  MODEL SERVING                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │              FastAPI Application                 │       │
│  ├─────────────────────────────────────────────────┤       │
│  │  /predict     - Single machine prediction       │       │
│  │  /predict/batch - Fleet-wide predictions       │       │
│  │  /health/{id} - Machine health score           │       │
│  │  /telemetry   - Real-time data stream          │       │
│  │  /feedback    - User feedback collection       │       │
│  └────────────────────┬────────────────────────────┘       │
│                       │                                     │
│  ┌────────────────────▼────────────────────────────┐       │
│  │              Model Registry                      │       │
│  │  • XGBoost v1 (production)                      │       │
│  │  • XGBoost v2 (shadow)                          │       │
│  │  • Isolation Forest (anomaly backup)            │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Serving Strategy:**
- Primary model: XGBoost for failure prediction
- Shadow model: New versions run in parallel before promotion
- Fallback: Threshold-based alerting if model unavailable

### 4. Dashboard & Decision Support

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (React)                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │  Mission Control Console                          │      │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐    │      │
│  │  │ Health     │ │ Telemetry  │ │ Alert      │    │      │
│  │  │ Gauges     │ │ Charts     │ │ Timeline   │    │      │
│  │  └────────────┘ └────────────┘ └────────────┘    │      │
│  │                                                   │      │
│  │  ┌────────────────────────────────────────────┐  │      │
│  │  │  AI Insight Panel                          │  │      │
│  │  │  • Risk explanation                        │  │      │
│  │  │  • Feature contributions                   │  │      │
│  │  │  • Recommended actions                     │  │      │
│  │  └────────────────────────────────────────────┘  │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Sensor → Kafka → Feature Store → Model → API → Dashboard
                      ↓                     ↑
                Time-series DB          User Feedback
                      ↓                     ↓
                Model Retraining ←──────────┘
```

## Failure Modes & Mitigations

| Component | Failure Mode | Detection | Mitigation |
|-----------|--------------|-----------|------------|
| Kafka | Broker down | Connection timeout | Retry with backoff, alert |
| Feature Store | Cache miss | Redis MISS | Compute on-demand |
| Model Service | High latency | P99 > 500ms | Queue requests, scale out |
| Model | Drift detected | Distribution shift | Alert, trigger retrain |
| API | Overload | 429 responses | Rate limiting, autoscale |

## Security Considerations

- All API endpoints require authentication (JWT)
- Sensor data encrypted in transit (TLS 1.3)
- Model artifacts signed and versioned
- Audit logging for all predictions
- No PII in telemetry data

## Deployment

### Container Architecture

```yaml
services:
  api:
    image: aegisops-api:latest
    replicas: 3
    resources:
      limits:
        cpu: 2
        memory: 4Gi
    healthcheck:
      path: /api/v1/system/status

  feature-worker:
    image: aegisops-features:latest
    replicas: 2

  dashboard:
    image: aegisops-frontend:latest
    replicas: 2
```

### Monitoring

- **Prometheus**: API latency, model inference time, feature computation
- **Grafana**: Dashboards for ops team
- **PagerDuty**: Alerting for system failures
- **MLflow**: Model performance tracking
