from __future__ import annotations

import datetime
import http

import argon2
import sanic

from backend import utils
from backend.db.queries import Queries  # noqa: TC001
from backend.internal import errors
from backend.internal import serialization
from shared.models import requests
from shared.models import responses

router = sanic.Blueprint("authentication")


WRONG_CREDENTIALS_ERROR = sanic.SanicException(
    message="Combination of username and password does not match", status_code=http.HTTPStatus.UNAUTHORIZED
)


@router.post("/login")
@serialization.serialize()
@serialization.deserialize()
async def login(_: sanic.Request, request_body: requests.LoginRequest, queries: Queries) -> responses.LoginResponse:
    """Login endpoint where the user gets his jwt token used for authentication.

    Authors: Christopher, Quirin
    """
    db_user = await queries.get_user_by_username(username=request_body.username)
    if db_user is None:
        raise WRONG_CREDENTIALS_ERROR

    try:
        utils.password_hasher.verify(db_user.password, request_body.password)
    except (argon2.exceptions.VerifyMismatchError, argon2.exceptions.VerificationError) as e:
        raise WRONG_CREDENTIALS_ERROR from e
    except argon2.exceptions.InvalidHashError as e:
        raise errors.InternalServerError(custom_code=errors.InternalServerErrorCodes.INVALID_HASH) from e

    token = utils.generate_token(user_id=db_user.id)
    return responses.LoginResponse(token=token, expires_at=datetime.datetime.now(datetime.UTC) + utils.DEFAULT_EXPIRY)
