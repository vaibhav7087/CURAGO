"""
backend/app/routers/predict.py
Decision-support severity prediction endpoint.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add ds/ to Python path so we can import predict module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from ds.predict import predict_severity, predict_disease

router = APIRouter()


class SeverityRequest(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    symptoms: Optional[str] = None
    temperature: Optional[float] = None
    pulse: Optional[int] = None
    respiratory_rate: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    spo2: Optional[float] = None
    pain_scale: Optional[int] = None


@router.post("/predict-severity")
async def predict_severity_endpoint(req: SeverityRequest):
    """
    DS-powered triage severity prediction.
    Returns model prediction + confidence alongside doctor's verdict.
    This is decision-support, NOT authority — doctor always overrides.
    """
    try:
        result = predict_severity(req.model_dump())
        return {
            "status": "ok",
            "prediction": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DiseaseRequest(BaseModel):
    text: str


@router.post("/predict-disease")
async def predict_disease_endpoint(req: DiseaseRequest):
    """
    Symptom-text -> disease (Symptom2Disease model, 24 diseases).
    Decision-support only — doctor always overrides.
    """
    try:
        result = predict_disease(req.text)
        return {
            "status": "ok",
            "prediction": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
