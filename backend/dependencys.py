from __future__ import annotations

__all__ = ("get_current_user",)

import http
import typing

import jwt
import sanic

from backend import utils
from backend.db.queries import Queries  # noqa: TC001

if typing.TYPE_CHECKING:
    from backend.db import models

INVALID_TOKEN_ERROR = sanic.SanicException(message="Invalid token.", status_code=http.HTTPStatus.UNAUTHORIZED)


async def get_current_user(request: sanic.Request, queries: Queries) -> models.User:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise sanic.SanicException(message="Authorization header is missing.", status_code=http.HTTPStatus.UNAUTHORIZED)
    token = auth_header.split(" ")[-1]
    try:
        user_id = utils.decode_token(token)
    except jwt.exceptions.PyJWTError:
        raise INVALID_TOKEN_ERROR from None
    else:
        db_user = await queries.get_user_by_id(id_=user_id)
        if not db_user:
            raise INVALID_TOKEN_ERROR
        return db_user
