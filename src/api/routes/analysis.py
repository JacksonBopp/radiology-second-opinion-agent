from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.agent.orchestrator import run_analysis_graph
from src.api.auth import AuthenticatedUser, get_current_user

router = APIRouter(prefix="/analyze", tags=["analysis"])


class AnalysisRequest(BaseModel):
    """Payload for triggering an agentic reasoning analysis."""

    scan_id: str = Field(..., description="Unique identifier for the scan")
    findings: list[dict] = Field(
        default_factory=list, description="Findings from the ML vision pipeline"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Scan and patient metadata"
    )


@router.post("")
def trigger_analysis(
    request: AnalysisRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Trigger the LangGraph analysis pipeline for a scan."""
    try:
        result = run_analysis_graph(
            scan_id=request.scan_id,
            findings=request.findings,
            metadata=request.metadata,
        )
        return {"status": "success", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
