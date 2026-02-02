"""
Prediction API Routes
Handles failure prediction requests and model inference
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

router = APIRouter()


class FeatureVector(BaseModel):
    """Input features for prediction."""
    vibration_rms: float = Field(..., description="RMS vibration (mm/s)")
    vibration_peak: float = Field(..., description="Peak vibration amplitude")
    vibration_kurtosis: float = Field(..., description="Vibration kurtosis")
    temperature: float = Field(..., description="Component temperature (C)")
    temp_rate_of_change: float = Field(..., description="Temperature gradient (C/min)")
    power_consumption: float = Field(..., description="Power draw (kW)")
    power_deviation: float = Field(..., description="Deviation from baseline (%)")
    time_since_maintenance: float = Field(..., description="Hours since last PM")
    cumulative_cycles: int = Field(..., description="Total cycles since overhaul")


class PredictionRequest(BaseModel):
    """Prediction request schema."""
    machine_id: str = Field(..., description="Machine identifier")
    features: FeatureVector
    request_explanation: bool = Field(default=True, description="Include SHAP explanation")


class PredictionResponse(BaseModel):
    """Prediction response schema."""
    prediction_id: str
    machine_id: str
    timestamp: str
    risk_score: float = Field(..., ge=0, le=100, description="Risk score 0-100")
    failure_probability: float = Field(..., ge=0, le=1, description="P(failure) in next 72h")
    risk_level: str = Field(..., description="low/medium/high/critical")
    recommended_action: str
    explanation: Optional[Dict[str, Any]] = None
    confidence: float = Field(..., ge=0, le=1)


class BatchPredictionRequest(BaseModel):
    """Batch prediction request."""
    machines: List[PredictionRequest]


@router.post("/predict", response_model=PredictionResponse)
async def predict_failure(request: PredictionRequest):
    """
    Generate failure prediction for a machine.

    Returns risk score, failure probability, and actionable recommendations
    with SHAP-based explanations for model transparency.
    """
    # Simulate model inference
    features = request.features

    # Risk calculation (simplified - real model would use XGBoost)
    vibration_risk = (features.vibration_rms / 50) * 30
    temp_risk = max(0, (features.temperature - 45) / 30) * 25
    maintenance_risk = min(features.time_since_maintenance / 500, 1) * 20
    kurtosis_risk = max(0, (features.vibration_kurtosis - 3) / 5) * 25

    risk_score = min(100, vibration_risk + temp_risk + maintenance_risk + kurtosis_risk)
    failure_prob = risk_score / 100 * 0.85  # Scale to probability

    # Determine risk level
    if risk_score < 25:
        risk_level = "low"
        action = "Continue normal operations. Next scheduled PM in queue."
    elif risk_score < 50:
        risk_level = "medium"
        action = "Increase monitoring frequency. Schedule inspection within 7 days."
    elif risk_score < 75:
        risk_level = "high"
        action = "Schedule preventive maintenance within 48 hours. Reduce load if possible."
    else:
        risk_level = "critical"
        action = "IMMEDIATE ACTION: Stop production and perform emergency inspection."

    # Generate explanation
    explanation = None
    if request.request_explanation:
        explanation = {
            "feature_contributions": {
                "vibration_kurtosis": round(kurtosis_risk, 2),
                "vibration_rms": round(vibration_risk, 2),
                "temperature": round(temp_risk, 2),
                "time_since_maintenance": round(maintenance_risk, 2),
                "power_deviation": round(features.power_deviation * 5, 2)
            },
            "top_factors": [
                f"Vibration kurtosis ({features.vibration_kurtosis:.2f}) indicates potential bearing wear",
                f"RMS vibration elevated at {features.vibration_rms:.1f} mm/s",
                f"{features.time_since_maintenance:.0f} hours since last maintenance"
            ],
            "natural_language": generate_explanation(features, risk_level)
        }

    return PredictionResponse(
        prediction_id=str(uuid.uuid4()),
        machine_id=request.machine_id,
        timestamp=datetime.utcnow().isoformat(),
        risk_score=round(risk_score, 1),
        failure_probability=round(failure_prob, 3),
        risk_level=risk_level,
        recommended_action=action,
        explanation=explanation,
        confidence=0.87
    )


@router.post("/predict/batch")
async def predict_batch(request: BatchPredictionRequest):
    """Batch prediction for multiple machines."""
    results = []
    for machine_request in request.machines:
        result = await predict_failure(machine_request)
        results.append(result)

    return {
        "batch_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(results),
        "predictions": results,
        "summary": {
            "critical": sum(1 for r in results if r.risk_level == "critical"),
            "high": sum(1 for r in results if r.risk_level == "high"),
            "medium": sum(1 for r in results if r.risk_level == "medium"),
            "low": sum(1 for r in results if r.risk_level == "low")
        }
    }


def generate_explanation(features: FeatureVector, risk_level: str) -> str:
    """Generate natural language explanation for operations staff."""
    explanations = []

    if features.vibration_kurtosis > 4:
        explanations.append(
            f"Elevated vibration kurtosis ({features.vibration_kurtosis:.2f}) suggests "
            "early-stage bearing degradation with impulsive vibration patterns."
        )

    if features.vibration_rms > 25:
        explanations.append(
            f"RMS vibration ({features.vibration_rms:.1f} mm/s) exceeds baseline threshold, "
            "indicating potential mechanical looseness or imbalance."
        )

    if features.temperature > 55:
        explanations.append(
            f"Operating temperature ({features.temperature:.1f}C) is elevated, "
            "which may accelerate component wear."
        )

    if features.time_since_maintenance > 400:
        explanations.append(
            f"Extended time since last PM ({features.time_since_maintenance:.0f} hours) "
            "increases probability of undetected wear accumulation."
        )

    if not explanations:
        return "All monitored parameters within normal operating ranges."

    return " ".join(explanations)
