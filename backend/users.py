from __future__ import annotations

import sanic

from backend import utils
from backend.db import models  # noqa: TC001
from backend.internal import serialization
from shared.models import responses

router = sanic.Blueprint("users")


@router.get("/me")
@serialization.serialize()
async def get_me(_: sanic.Request, user: models.User) -> responses.PublicUser:
    """Get the current user's information."""
    return utils.convert_struct(user, responses.PublicUser)
