from __future__ import annotations

import http

import argon2
import sanic

from backend import utils
from backend.db import models  # noqa: TC001
from backend.db.queries import Queries  # noqa: TC001
from backend.internal import errors
from backend.internal import serialization
from shared.internal import snowflakes
from shared.models import requests
from shared.models import responses

router = sanic.Blueprint("users")


@router.get("/me")
@serialization.serialize()
async def get_me(_: sanic.Request, user: models.User) -> responses.PublicUser:
    """Get the current user's information.

    Authors: Christopher
    """
    return utils.convert_struct(user, responses.PublicUser)


@router.post("/")
@serialization.deserialize()
async def create_user(_: sanic.Request, request_body: requests.LoginRequest, queries: Queries) -> sanic.HTTPResponse:
    """Endpoint to create a new user.

    This checks if the username is available and hashes the password and then adds the user to the db.

    Authors: Quirin
    """
    db_user = await queries.get_user_by_username(username=request_body.username)
    if db_user is not None:
        raise sanic.SanicException(message="Username already exists", status_code=http.HTTPStatus.CONFLICT)

    user_id = snowflakes.generate_snowflake()
    try:
        hashed_user_pw = utils.password_hasher.hash(request_body.password)
    except argon2.exceptions.HashingError as e:
        raise errors.InternalServerError(custom_code=errors.InternalServerErrorCodes.HASHING_FAILED) from e

    await queries.create_user(id_=user_id, username=request_body.username, password=hashed_user_pw, money=1000)
    await queries.conn.commit()
    return sanic.empty()
