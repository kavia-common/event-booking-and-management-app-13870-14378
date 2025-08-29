from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from src.domain.models import EventStatus


class TicketTypeBase(BaseModel):
    name: str = Field(..., description="Ticket type name")
    price: float = Field(..., ge=0.0, description="Ticket price")
    currency: str = Field("USD", description="Currency code, e.g., USD")
    quantity_total: int = Field(0, ge=0, description="Total quantity available")


class TicketTypeCreate(TicketTypeBase):
    pass


class TicketTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Ticket type name")
    price: Optional[float] = Field(None, ge=0.0, description="Ticket price")
    currency: Optional[str] = Field(None, description="Currency code")
    quantity_total: Optional[int] = Field(None, ge=0, description="Total quantity available")


class TicketTypePublic(BaseModel):
    id: str = Field(..., description="Ticket type ID")
    name: str
    price: float
    currency: str
    quantity_total: int
    quantity_sold: int
    quantity_available: int


class EventBase(BaseModel):
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    category: str = Field(..., description="Event category")
    location: str = Field(..., description="City or venue location")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")

    @field_validator("end_time")
    @classmethod
    def validate_times(cls, v: datetime, info):
        start_time = info.data.get("start_time")
        if start_time and v <= start_time:
            raise ValueError("end_time must be after start_time")
        return v


class EventCreate(EventBase):
    organizer_id: str = Field(..., description="Organizer user ID")
    status: EventStatus = Field(default=EventStatus.DRAFT, description="Initial event status")
    ticket_types: List[TicketTypeCreate] = Field(default_factory=list, description="Initial ticket types")


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    category: Optional[str] = Field(None, description="Event category")
    location: Optional[str] = Field(None, description="Location")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    tags: Optional[List[str]] = Field(None, description="Tags")
    status: Optional[EventStatus] = Field(None, description="Event status")
    ticket_types: Optional[List[TicketTypeUpdate]] = Field(None, description="Replace all ticket types (PUT-like behavior)")


class EventPublic(BaseModel):
    id: str
    organizer_id: str
    title: str
    description: str
    category: str
    location: str
    start_time: datetime
    end_time: datetime
    status: EventStatus
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    views: int
    favorites: int
    ticket_types: List[TicketTypePublic]


class EventList(BaseModel):
    total: int = Field(..., description="Total events matching filters")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    items: List[EventPublic] = Field(..., description="Events")


class AnalyticsSummary(BaseModel):
    event_id: str = Field(..., description="Event ID")
    total_views: int = Field(..., description="Views")
    total_favorites: int = Field(..., description="Favorites")
    total_capacity: int = Field(..., description="Sum of ticket quantities")
    total_sold: int = Field(..., description="Sum of sold")
    total_available: int = Field(..., description="Remaining capacity")


class PlatformAnalytics(BaseModel):
    total_events: int
    by_status: dict
    top_categories: List[dict]
