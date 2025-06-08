from __future__ import annotations

import datetime
import http

import sanic
from shared.internal import generate_snowflake
from argon2 import PasswordHasher
from backend import utils
from backend.db.queries import Queries  # noqa: TC001
from backend.internal import serialization
from shared import models

router = sanic.Blueprint("authentication")

ph = PasswordHasher()

WRONG_CREDENTIALS_ERROR = sanic.SanicException(
    message="Combination of username and password does not match", status_code=http.HTTPStatus.UNAUTHORIZED
)


@router.post("/login")
@serialization.serialize()
@serialization.deserialize()
async def login(_: sanic.Request, request_body: models.LoginRequest, queries: Queries) -> models.LoginResponse:
    db_user = await queries.get_user_by_username(username=request_body.username)
    if db_user is None:
        raise WRONG_CREDENTIALS_ERROR

    # Verify the password
    try:
        ph.verify(db_user.password, request_body.password)
    except Exception:
        raise WRONG_CREDENTIALS_ERROR
    

    token = utils.generate_token(user_id=db_user.id)
    return models.LoginResponse(
        token=token,
        expires_at=datetime.datetime.now(datetime.UTC) + utils.DEFAULT_EXPIRY
    )


@router.post("/register")
@serialization.serialize()
@serialization.deserialize()
async def register(_: sanic.Request, request_body: models.LoginRequest, queries: Queries) -> models.Success:
    db_user = await queries.get_user_by_username(username=request_body.username)
    if db_user is not None:
        raise sanic.SanicException(
            message="Username already exists",
            status_code=http.HTTPStatus.CONFLICT
        )

    user_id = generate_snowflake()
    hashed_user_pw = ph.hash(request_body.password)

    await queries.create_user(id_=user_id, username=request_body.username, password=hashed_user_pw, money=1000)
    await queries.conn.commit()

    return models.Success(
        message="User registered successfully"
    )
