# Event Service

Event lifecycle management, discovery, and analytics for the platform.

## Features

- Organizers:
  - Create, update, delete events
  - List their events
  - View event analytics summary
- Attendees:
  - Discover/search events with filters and pagination
  - View event details (views counted)
  - Favorite / unfavorite events
- Administrators:
  - Platform-wide analytics

## Security model (dev-friendly)

This service expects user identity/roles to be provided by the API Gateway. For local development and testing, you can pass headers:

- `x-user-id`: current user ID
- `x-user-roles`: comma-separated roles, e.g. `attendee,organizer`
- Optionally, `x-api-key` if `INTERNAL_API_KEY` is set in the environment

Role helpers:
- Organizer: `organizer` or `admin`
- Admin: `admin`
- Attendee: `attendee`, `organizer`, or `admin`

## API Summary

- Health:
  - GET `/` — health check
  - GET `/docs/websocket-usage` — note about WebSocket usage (none currently)
- Events:
  - POST `/events` — create event (organizer/admin)
  - GET `/events/{event_id}` — get event (increments views by default)
  - GET `/events` — discovery with filters and pagination
  - PATCH `/events/{event_id}` — update event (organizer/admin)
  - DELETE `/events/{event_id}` — delete event (organizer/admin)
  - POST `/events/{event_id}/favorite` — favorite (attendee)
  - POST `/events/{event_id}/unfavorite` — unfavorite (attendee)
  - GET `/events/organizer/{organizer_id}` — list organizer events (self or admin)
  - GET `/events/{event_id}/analytics/summary` — organizer/admin analytics
- Admin:
  - GET `/admin/analytics` — platform analytics (admin)

OpenAPI spec can be generated via:
```
python -m src.api.generate_openapi
```
This writes the file to `interfaces/openapi.json`.

## Running locally

Install dependencies (see requirements.txt), then:
```
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

You can test with curl:
```
# Create an event as organizer
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "x-user-id: org-1" -H "x-user-roles: organizer" \
  -d '{
    "organizer_id": "org-1",
    "title": "Tech Conference",
    "description": "All about tech.",
    "category": "Technology",
    "location": "Berlin",
    "start_time": "2030-01-01T10:00:00Z",
    "end_time": "2030-01-01T18:00:00Z",
    "tags": ["tech","conference"],
    "ticket_types": [{"name":"General","price":99.0,"currency":"USD","quantity_total":100}]
  }'
```

## Notes

- Storage is in-memory for demonstration and CI. Replace `InMemoryDB` with a real database integration as needed.
- Keep environment variables in `.env` (do not commit secrets).
