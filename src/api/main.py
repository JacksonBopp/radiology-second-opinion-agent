from fastapi import FastAPI, File, HTTPException, UploadFile

from src.ingestion.pipeline import process_scan_bytes

app = FastAPI(title="Radiology Second-Opinion Agent API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/scans")
async def upload_scan(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        return process_scan_bytes(file.filename or "scan.dcm", content)
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Could not process DICOM file: {exc}"
        ) from exc
