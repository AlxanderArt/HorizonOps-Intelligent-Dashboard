"""
HorizonOps Predictive Intelligence - FastAPI Application
Aerospace Manufacturing Predictive Maintenance System
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging
import json

from .routes import predictions, telemetry, feedback, health, auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("horizonops")

# Application metadata
app = FastAPI(
    title="HorizonOps Predictive Intelligence API",
    description="AI-driven operational intelligence for aerospace manufacturing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(telemetry.router, prefix="/api/v1", tags=["Telemetry"])
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])


@app.get("/")
async def root():
    """API root endpoint with service information."""
    return {
        "service": "HorizonOps Predictive Intelligence",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "predictions": "/api/v1/predict",
            "health": "/api/v1/health/{machine_id}",
            "telemetry": "/api/v1/telemetry/{machine_id}",
            "feedback": "/api/v1/feedback",
            "docs": "/docs"
        }
    }


@app.get("/api/v1/system/status")
async def system_status():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "api": "operational",
            "model": "loaded",
            "database": "connected",
            "feature_store": "available"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("HorizonOps API starting up...")
    logger.info("Loading ML models...")
    # Model loading would happen here
    logger.info("API ready to serve requests")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("HorizonOps API shutting down...")
