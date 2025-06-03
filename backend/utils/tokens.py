from __future__ import annotations

import datetime

import jwt

from shared.internal import Snowflake

SECRET_KEY = "SSj,4MdH)pfe@c.edBwX#_D%0+_L?[b]m6t#J2tCbhy=9)b8VFud+J,&Dzu;"
DEFAULT_EXPIRY = datetime.timedelta(days=1)

__all__ = ("decode_token", "generate_token")


def generate_token(user_id: Snowflake) -> str:
    return jwt.encode(
        payload={"user_id": user_id, "exp": datetime.datetime.now(datetime.UTC) + DEFAULT_EXPIRY},
        key=SECRET_KEY,
        algorithm="HS256",
    )


def decode_token(token: str) -> Snowflake:
    payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=("HS256",))
    if user_id := payload.get("user_id"):
        return Snowflake(user_id)
    raise jwt.exceptions.PyJWTError
