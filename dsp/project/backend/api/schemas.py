from pydantic import BaseModel


class PredictionResponse(BaseModel):
    prediction: str
    total_windows: int
    seizure_windows: int
    seizure_windows_pct: float
    avg_seizure_probability: float
    max_seizure_probability: float
    confidence: float
    risk_level: str
    threshold_used: float
    filename: str


class ErrorResponse(BaseModel):
    detail: str
