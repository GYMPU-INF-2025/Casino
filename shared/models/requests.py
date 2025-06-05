from __future__ import annotations

__all__ = (
    "LoginRequest",
)

import msgspec

class LoginRequest(msgspec.Struct):
    """Request for login."""
    
    username: str
    password: str