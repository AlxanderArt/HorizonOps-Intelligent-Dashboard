"""
Feedback API Routes
Handles user feedback collection for model improvement
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter()

# In-memory feedback storage (would be database in production)
feedback_store = []


class FeedbackRequest(BaseModel):
    """User feedback on a prediction."""
    prediction_id: str = Field(..., description="ID of the prediction being evaluated")
    machine_id: str = Field(..., description="Machine that was predicted on")
    actual_outcome: str = Field(..., description="What actually happened: 'failure', 'no_failure', 'maintenance_performed'")
    was_prediction_accurate: bool = Field(..., description="Did the prediction match reality?")
    user_notes: Optional[str] = Field(None, description="Additional context from operator")
    action_taken: Optional[str] = Field(None, description="What action did operations take?")
    time_to_event: Optional[float] = Field(None, description="Hours between prediction and actual event")


class FeedbackResponse(BaseModel):
    """Response after feedback submission."""
    feedback_id: str
    status: str
    message: str
    timestamp: str


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit feedback on a prediction outcome.

    This data is used to:
    1. Track model performance metrics
    2. Generate training labels for model retraining
    3. Identify prediction patterns that need improvement
    """
    feedback_id = str(uuid.uuid4())

    feedback_record = {
        "feedback_id": feedback_id,
        "prediction_id": feedback.prediction_id,
        "machine_id": feedback.machine_id,
        "actual_outcome": feedback.actual_outcome,
        "was_accurate": feedback.was_prediction_accurate,
        "user_notes": feedback.user_notes,
        "action_taken": feedback.action_taken,
        "time_to_event": feedback.time_to_event,
        "submitted_at": datetime.utcnow().isoformat(),
        "processed": False
    }

    feedback_store.append(feedback_record)

    return FeedbackResponse(
        feedback_id=feedback_id,
        status="accepted",
        message="Feedback recorded. Thank you for improving the model.",
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/feedback/statistics")
async def get_feedback_statistics():
    """
    Get aggregated feedback statistics for model performance monitoring.
    """
    if not feedback_store:
        return {
            "total_feedback": 0,
            "accuracy_rate": None,
            "message": "No feedback collected yet"
        }

    total = len(feedback_store)
    accurate = sum(1 for f in feedback_store if f["was_accurate"])

    outcomes = {}
    for f in feedback_store:
        outcome = f["actual_outcome"]
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_feedback": total,
        "accuracy_rate": round(accurate / total, 3) if total > 0 else None,
        "outcome_distribution": outcomes,
        "recent_feedback_count": sum(1 for f in feedback_store[-100:] if f["was_accurate"]),
        "model_performance": {
            "true_positives": sum(1 for f in feedback_store if f["actual_outcome"] == "failure" and f["was_accurate"]),
            "false_positives": sum(1 for f in feedback_store if f["actual_outcome"] == "no_failure" and not f["was_accurate"]),
            "true_negatives": sum(1 for f in feedback_store if f["actual_outcome"] == "no_failure" and f["was_accurate"]),
            "false_negatives": sum(1 for f in feedback_store if f["actual_outcome"] == "failure" and not f["was_accurate"])
        }
    }


@router.get("/feedback/recent")
async def get_recent_feedback(limit: int = 20):
    """Get most recent feedback submissions."""
    recent = sorted(feedback_store, key=lambda x: x["submitted_at"], reverse=True)[:limit]

    return {
        "count": len(recent),
        "feedback": recent
    }


@router.get("/feedback/export")
async def export_training_labels():
    """
    Export feedback data formatted for model retraining.

    Returns labeled examples that can be used to improve model accuracy.
    """
    training_data = []

    for f in feedback_store:
        if f["actual_outcome"] in ["failure", "no_failure"]:
            training_data.append({
                "prediction_id": f["prediction_id"],
                "machine_id": f["machine_id"],
                "label": 1 if f["actual_outcome"] == "failure" else 0,
                "feedback_timestamp": f["submitted_at"],
                "time_to_event_hours": f.get("time_to_event")
            })

    return {
        "export_timestamp": datetime.utcnow().isoformat(),
        "record_count": len(training_data),
        "training_labels": training_data
    }


@router.post("/feedback/acknowledge/{prediction_id}")
async def acknowledge_alert(prediction_id: str, user_id: Optional[str] = None):
    """Mark a prediction/alert as acknowledged by an operator."""
    return {
        "status": "acknowledged",
        "prediction_id": prediction_id,
        "acknowledged_by": user_id or "anonymous",
        "acknowledged_at": datetime.utcnow().isoformat()
    }
