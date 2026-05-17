from fastapi import APIRouter
from schemas import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthStatus, summary="Health check")
async def health_check():
    """Returns server health status."""
    return HealthStatus(status="ok")
