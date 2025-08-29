from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import events as events_routes
from src.api.routes import admin as admin_routes
from src.core.config import get_settings

settings = get_settings()

openapi_tags = [
    {"name": "health", "description": "Service health and metadata"},
    {"name": "events", "description": "Event lifecycle and discovery endpoints"},
    {"name": "admin", "description": "Administrative analytics and operations"},
]

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.get("/", tags=["health"], summary="Health check", description="Simple health check endpoint.")
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


@app.get(
    "/docs/websocket-usage",
    tags=["health"],
    summary="WebSocket usage notes",
    description="This service currently does not expose WebSockets. This endpoint is reserved for documenting real-time features in the future.",
)
def websocket_usage_note():
    """WebSocket usage notes for OpenAPI."""
    return {"message": "No WebSocket endpoints currently exposed."}


# Register routers
app.include_router(events_routes.router)
app.include_router(admin_routes.router)
