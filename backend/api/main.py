import os
import sys
import shutil
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.infer import SeizureInferenceEngine
from api.schemas import PredictionResponse

ARTIFACTS_DIR = os.environ.get("ARTIFACTS_DIR", "artifacts")
ALLOWED_EXTENSIONS = {".mat", ".csv"}
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200MB — real patient .mat recordings run 60-115MB+

app = FastAPI(title="NeuroSense AI — Seizure Detection API")

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in ALLOWED_ORIGINS.split(",")] if ALLOWED_ORIGINS != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # set ALLOWED_ORIGINS env var to your Netlify URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        if not os.path.isdir(ARTIFACTS_DIR):
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Model artifacts not found at '{ARTIFACTS_DIR}/'. "
                    "Run `python ml/train.py --data_dir <path_to_mat_files>` first."
                ),
            )
        _engine = SeizureInferenceEngine(artifacts_dir=ARTIFACTS_DIR)
    return _engine


@app.get("/health")
def health():
    try:
        engine = get_engine()
        return {"status": "ok", "threshold": engine.threshold}
    except HTTPException as e:
        return {"status": "not_ready", "detail": e.detail}


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    engine = get_engine()

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit.")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = engine.predict(tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        os.remove(tmp_path)

    result["filename"] = file.filename
    return result
