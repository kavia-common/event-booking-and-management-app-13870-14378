from fastapi import APIRouter, Depends

from src.security.deps import CurrentUser, require_admin
from src.services.events import platform_analytics

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/analytics",
    summary="Platform analytics (admin)",
    description="Aggregate analytics across all events, categories, and statuses.",
)
def platform_analytics_endpoint(user: CurrentUser = Depends(require_admin)) -> dict:
    """Return aggregated platform analytics across events."""
    return platform_analytics(user)
