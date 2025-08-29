from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from src.domain.schemas import (
    AnalyticsSummary,
    EventCreate,
    EventList,
    EventPublic,
    EventUpdate,
)
from src.security.deps import CurrentUser, get_current_user, require_organizer
from src.services import events as svc

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=EventPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create an event",
    description="Create a new event. Organizer can only create for themselves unless admin.",
)
def create_event_endpoint(payload: EventCreate, user: CurrentUser = Depends(require_organizer)) -> EventPublic:
    """Create a new event. Organizer role required."""
    return svc.create_event(payload, user)


@router.get(
    "/{event_id}",
    response_model=EventPublic,
    summary="Get event by ID",
    description="Retrieve an event by ID. Public endpoint increments views by default.",
)
def get_event_endpoint(event_id: str, increment_view: bool = True) -> EventPublic:
    """Get event details; optionally increments the views counter for analytics."""
    return svc.get_event(event_id, increment_view=increment_view)


@router.get(
    "",
    response_model=EventList,
    summary="Search and list events",
    description="Public discovery endpoint supporting text search, filters, sorting, and pagination.",
)
def list_events_endpoint(
    q: Optional[str] = Query(None, description="Free text query on title/description"),
    category: Optional[str] = Query(None, description="Category filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    status_filter: Optional[str] = Query(None, description="Event status"),
    start_from: Optional[datetime] = Query(None, description="Start time from (inclusive)"),
    start_to: Optional[datetime] = Query(None, description="Start time to (inclusive)"),
    tags: Optional[List[str]] = Query(None, description="Require all of these tags"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: Optional[str] = Query(None, description="Sort by: start_time|created_at|views|favorites"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
) -> EventList:
    """Discover events with filters and pagination."""
    # normalized status enum if provided
    from src.domain.models import EventStatus

    enum_status = EventStatus(status_filter) if status_filter else None
    return svc.list_events(
        q=q,
        category=category,
        location=location,
        status_filter=enum_status,
        start_from=start_from,
        start_to=start_to,
        tags=tags,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.patch(
    "/{event_id}",
    response_model=EventPublic,
    summary="Update an event",
    description="Organizer can update their own events; admins can update any.",
)
def update_event_endpoint(
    event_id: str,
    payload: EventUpdate,
    user: CurrentUser = Depends(require_organizer),
) -> EventPublic:
    """Update event fields."""
    return svc.update_event(event_id, payload, user)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event",
    description="Organizer can delete their own events; admins can delete any.",
)
def delete_event_endpoint(event_id: str, user: CurrentUser = Depends(require_organizer)) -> None:
    """Delete an event."""
    svc.delete_event(event_id, user)
    return None


@router.post(
    "/{event_id}/favorite",
    response_model=EventPublic,
    summary="Favorite an event",
    description="Attendee favorites an event (increments favorites count).",
)
def favorite_event_endpoint(event_id: str, user: CurrentUser = Depends(get_current_user)) -> EventPublic:
    """Favorite an event."""
    return svc.favorite_event(event_id, user)


@router.post(
    "/{event_id}/unfavorite",
    response_model=EventPublic,
    summary="Unfavorite an event",
    description="Attendee removes favorite (decrements favorites count).",
)
def unfavorite_event_endpoint(event_id: str, user: CurrentUser = Depends(get_current_user)) -> EventPublic:
    """Unfavorite an event."""
    return svc.unfavorite_event(event_id, user)


@router.get(
    "/organizer/{organizer_id}",
    response_model=EventList,
    summary="List organizer events",
    description="Organizer can list and manage their own events. Admins can view any organizer's events.",
)
def organizer_events_endpoint(
    organizer_id: str,
    status_filter: Optional[str] = Query(None, description="Event status filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(require_organizer),
) -> EventList:
    """List events belonging to an organizer."""
    from src.domain.models import EventStatus

    enum_status = EventStatus(status_filter) if status_filter else None
    return svc.organizer_events(organizer_id, enum_status, page, page_size, user)


@router.get(
    "/{event_id}/analytics/summary",
    response_model=AnalyticsSummary,
    summary="Event analytics summary",
    description="Organizer-only analytics for an event (admin can access any).",
)
def analytics_summary_endpoint(
    event_id: str, user: CurrentUser = Depends(require_organizer)
) -> AnalyticsSummary:
    """Simple event analytics."""
    return svc.analytics_summary(event_id, user)
