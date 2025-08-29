from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from src.core.config import get_settings


class CurrentUser:
    """Represents current user claims passed from API Gateway.
    In this simplified service, we accept user data via headers for dev/testing.
    In production, integrate with real auth (JWT verification or GW introspection).
    """
    def __init__(self, user_id: str, roles: list[str]):
        self.user_id = user_id
        self.roles = roles

    def is_admin(self) -> bool:
        return "admin" in self.roles

    def is_organizer(self) -> bool:
        return "organizer" in self.roles or self.is_admin()

    def is_attendee(self) -> bool:
        return "attendee" in self.roles or self.is_admin() or self.is_organizer()


# PUBLIC_INTERFACE
def get_current_user(
    x_user_id: Optional[str] = Header(default=None, alias="x-user-id"),
    x_user_roles: Optional[str] = Header(default="", alias="x-user-roles"),
    x_api_key: Optional[str] = Header(default=None, alias=None),
) -> CurrentUser:
    """Derive current user from headers.
    Headers:
    - x-user-id: user identifier (required for protected endpoints)
    - x-user-roles: comma-separated roles (attendee,organizer,admin)
    - x-api-key: optional internal key enforcement if configured
    """
    settings = get_settings()

    # Enforce internal API key if configured for protected endpoints
    if settings.INTERNAL_API_KEY and x_api_key and x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    if not x_user_id:
        # Anonymous user; limited access for public endpoints only.
        return CurrentUser(user_id="anonymous", roles=[])

    roles = [r.strip() for r in x_user_roles.split(",") if r.strip()]
    return CurrentUser(user_id=x_user_id, roles=roles)


# PUBLIC_INTERFACE
def require_organizer(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Ensure the current user has organizer privileges."""
    if not user.is_organizer():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organizer role required")
    return user


# PUBLIC_INTERFACE
def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Ensure the current user has admin privileges."""
    if not user.is_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user
