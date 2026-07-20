from fastapi import Depends, FastAPI, File, HTTPException, UploadFile

from src.api.auth import AuthenticatedUser, get_current_user
from src.api.audit import AuditLogMiddleware
from src.api.feedback import FeedbackIn, FeedbackOut, list_feedback, save_feedback
from src.ingestion.pipeline import process_scan_bytes
from src.api.routes.analysis import router as analysis_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Radiology Second-Opinion Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditLogMiddleware)

app.include_router(analysis_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/scans")
async def upload_scan(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        return process_scan_bytes(file.filename or "scan.dcm", content)
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Could not process DICOM file: {exc}"
        ) from exc


@app.post("/feedback", response_model=FeedbackOut)
def submit_feedback(
    feedback: FeedbackIn,
    user: AuthenticatedUser = Depends(get_current_user),
) -> FeedbackOut:
    return save_feedback(feedback, reviewer=user.name)


@app.get("/feedback", response_model=list[FeedbackOut])
def get_feedback(
    scan_id: str | None = None,
    user: AuthenticatedUser = Depends(get_current_user),
) -> list[FeedbackOut]:
    return list_feedback(scan_id=scan_id)
