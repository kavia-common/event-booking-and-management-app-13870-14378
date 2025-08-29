from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List


class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELED = "canceled"
    ARCHIVED = "archived"


@dataclass
class TicketType:
    id: str
    name: str
    price: float
    currency: str = "USD"
    quantity_total: int = 0
    quantity_sold: int = 0

    @property
    def quantity_available(self) -> int:
        return max(self.quantity_total - self.quantity_sold, 0)


@dataclass
class Event:
    id: str
    organizer_id: str
    title: str
    description: str
    category: str
    location: str
    start_time: datetime
    end_time: datetime
    status: EventStatus = EventStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    ticket_types: List[TicketType] = field(default_factory=list)
    # Simplified counters for analytics
    views: int = 0
    favorites: int = 0


class InMemoryDB:
    """A simple in-memory storage to simulate persistence."""
    def __init__(self) -> None:
        self.events: Dict[str, Event] = {}

    def generate_id(self) -> str:
        return str(uuid.uuid4())


# A single DB instance for the service lifetime
DB = InMemoryDB()
