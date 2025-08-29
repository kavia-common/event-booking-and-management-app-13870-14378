from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from src.domain.models import DB, Event, EventStatus, TicketType
from src.domain.schemas import (
    AnalyticsSummary,
    EventCreate,
    EventList,
    EventPublic,
    EventUpdate,
    TicketTypePublic,
)
from src.security.deps import CurrentUser


def _to_ticket_public(t: TicketType) -> TicketTypePublic:
    return TicketTypePublic(
        id=t.id,
        name=t.name,
        price=t.price,
        currency=t.currency,
        quantity_total=t.quantity_total,
        quantity_sold=t.quantity_sold,
        quantity_available=t.quantity_available,
    )


def _to_event_public(e: Event) -> EventPublic:
    return EventPublic(
        id=e.id,
        organizer_id=e.organizer_id,
        title=e.title,
        description=e.description,
        category=e.category,
        location=e.location,
        start_time=e.start_time,
        end_time=e.end_time,
        status=e.status,
        created_at=e.created_at,
        updated_at=e.updated_at,
        tags=e.tags,
        views=e.views,
        favorites=e.favorites,
        ticket_types=[_to_ticket_public(t) for t in e.ticket_types],
    )


def _paginate(items: List[Event], page: int, page_size: int) -> Tuple[List[Event], int]:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total


# PUBLIC_INTERFACE
def create_event(payload: EventCreate, user: CurrentUser) -> EventPublic:
    """Create a new event by organizer or admin."""
    # Organizers can only create for themselves unless admin
    if not user.is_admin() and payload.organizer_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create for another organizer")

    eid = DB.generate_id()
    ticket_types: List[TicketType] = []
    for t in payload.ticket_types:
        ticket_types.append(
            TicketType(
                id=DB.generate_id(),
                name=t.name,
                price=t.price,
                currency=t.currency,
                quantity_total=t.quantity_total,
                quantity_sold=0,
            )
        )

    e = Event(
        id=eid,
        organizer_id=payload.organizer_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        location=payload.location,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status=payload.status,
        tags=payload.tags or [],
        ticket_types=ticket_types,
    )
    DB.events[eid] = e
    return _to_event_public(e)


# PUBLIC_INTERFACE
def get_event(event_id: str, increment_view: bool = False) -> EventPublic:
    """Get event by ID. Optionally increment views for analytics."""
    e = DB.events.get(event_id)
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if increment_view:
        e.views += 1
    return _to_event_public(e)


# PUBLIC_INTERFACE
def list_events(
    q: Optional[str],
    category: Optional[str],
    location: Optional[str],
    status_filter: Optional[EventStatus],
    start_from: Optional[datetime],
    start_to: Optional[datetime],
    tags: Optional[List[str]],
    page: int,
    page_size: int,
    sort_by: Optional[str],
    sort_dir: str = "desc",
) -> EventList:
    """Search and filter public events for discovery."""
    items = list(DB.events.values())

    # Only show non-archived events to public discovery
    items = [e for e in items if e.status in {EventStatus.DRAFT, EventStatus.PUBLISHED, EventStatus.CANCELED}]

    if q:
        ql = q.lower()
        items = [e for e in items if ql in e.title.lower() or ql in e.description.lower()]

    if category:
        items = [e for e in items if e.category.lower() == category.lower()]

    if location:
        items = [e for e in items if e.location.lower() == location.lower()]

    if status_filter:
        items = [e for e in items if e.status == status_filter]

    if start_from:
        items = [e for e in items if e.start_time >= start_from]

    if start_to:
        items = [e for e in items if e.start_time <= start_to]

    if tags:
        tagset = {t.lower() for t in tags}
        items = [e for e in items if tagset.issubset({tt.lower() for tt in e.tags})]

    # Sorting
    reverse = sort_dir.lower() != "asc"
    if sort_by in {"start_time", "created_at", "views", "favorites"}:
        items.sort(key=lambda e: getattr(e, sort_by), reverse=reverse)
    else:
        # default: start_time desc
        items.sort(key=lambda e: e.start_time, reverse=True)

    # Pagination
    page_items, total = _paginate(items, page, page_size)
    return EventList(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_event_public(e) for e in page_items],
    )


# PUBLIC_INTERFACE
def update_event(event_id: str, payload: EventUpdate, user: CurrentUser) -> EventPublic:
    """Update event fields. Organizer can only modify own events."""
    e = DB.events.get(event_id)
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not user.is_admin() and e.organizer_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if payload.title is not None:
        e.title = payload.title
    if payload.description is not None:
        e.description = payload.description
    if payload.category is not None:
        e.category = payload.category
    if payload.location is not None:
        e.location = payload.location
    if payload.start_time is not None:
        e.start_time = payload.start_time
    if payload.end_time is not None:
        # ensure end_time after start_time if both set; EventUpdate validator is relaxed
        if payload.start_time and payload.end_time <= payload.start_time:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_time must be after start_time")
        if e.start_time and payload.end_time <= e.start_time:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_time must be after start_time")
        e.end_time = payload.end_time
    if payload.tags is not None:
        e.tags = payload.tags
    if payload.status is not None:
        e.status = payload.status
    if payload.ticket_types is not None:
        # replace all ticket types
        new_tts: List[TicketType] = []
        for t in payload.ticket_types:
            # For replace, generate new IDs (simplified)
            new_tts.append(
                TicketType(
                    id=DB.generate_id(),
                    name=t.name if t.name is not None else "General",
                    price=t.price if t.price is not None else 0.0,
                    currency=t.currency if t.currency is not None else "USD",
                    quantity_total=t.quantity_total if t.quantity_total is not None else 0,
                    quantity_sold=0,
                )
            )
        e.ticket_types = new_tts

    e.updated_at = datetime.utcnow()
    return _to_event_public(e)


# PUBLIC_INTERFACE
def delete_event(event_id: str, user: CurrentUser) -> None:
    """Delete an event. Organizer can delete only own events."""
    e = DB.events.get(event_id)
    if not e:
        return
    if not user.is_admin() and e.organizer_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    del DB.events[event_id]


# PUBLIC_INTERFACE
def favorite_event(event_id: str, user: CurrentUser) -> EventPublic:
    """Attendee favorites an event (toggle on)."""
    e = DB.events.get(event_id)
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    e.favorites += 1
    return _to_event_public(e)


# PUBLIC_INTERFACE
def unfavorite_event(event_id: str, user: CurrentUser) -> EventPublic:
    """Attendee removes favorite (toggle off)."""
    e = DB.events.get(event_id)
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    e.favorites = max(0, e.favorites - 1)
    return _to_event_public(e)


# PUBLIC_INTERFACE
def organizer_events(
    organizer_id: str,
    status_filter: Optional[EventStatus],
    page: int,
    page_size: int,
    user: CurrentUser,
) -> EventList:
    """List events belonging to an organizer. Organizer can only see own events unless admin."""
    if not user.is_admin() and organizer_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    items = [e for e in DB.events.values() if e.organizer_id == organizer_id]
    if status_filter:
        items = [e for e in items if e.status == status_filter]
    items.sort(key=lambda e: e.created_at, reverse=True)
    page_items, total = _paginate(items, page, page_size)
    return EventList(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_event_public(e) for e in page_items],
    )


# PUBLIC_INTERFACE
def analytics_summary(event_id: str, user: CurrentUser) -> AnalyticsSummary:
    """Return simple analytics for an event. Organizer-only for own event or admin."""
    e = DB.events.get(event_id)
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not user.is_admin() and e.organizer_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    total_capacity = sum(t.quantity_total for t in e.ticket_types)
    total_sold = sum(t.quantity_sold for t in e.ticket_types)
    total_available = sum(t.quantity_available for t in e.ticket_types)
    return AnalyticsSummary(
        event_id=e.id,
        total_views=e.views,
        total_favorites=e.favorites,
        total_capacity=total_capacity,
        total_sold=total_sold,
        total_available=total_available,
    )


# PUBLIC_INTERFACE
def platform_analytics(user: CurrentUser) -> dict:
    """Aggregate analytics across all events (admin only)."""
    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")

    total_events = len(DB.events)
    by_status = {}
    by_category = {}
    for e in DB.events.values():
        by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
        by_category[e.category] = by_category.get(e.category, 0) + 1

    top_categories = [
        {"category": k, "count": v}
        for k, v in sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)[:5]
    ]

    return {
        "total_events": total_events,
        "by_status": by_status,
        "top_categories": top_categories,
    }
