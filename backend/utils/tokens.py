from __future__ import annotations

__all__ = ("DEFAULT_EXPIRY", "decode_token", "generate_token")

import datetime

import jwt

from shared.internal import Snowflake

SECRET_KEY = "SSj,4MdH)pfe@c.edBwX#_D%0+_L?[b]m6t#J2tCbhy=9)b8VFud+J,&Dzu;"

DEFAULT_EXPIRY = datetime.timedelta(days=3)


def generate_token(user_id: Snowflake) -> str:
    """Generates a jwt token and stores the given user id in it.

    Authors: Christopher

    Parameters
    ----------
    user_id : Snowflake
        The user id that should be stored inside the jwt

    Returns
    -------
    str
        The encoded jwt token with the user id stored inside.

    """
    return jwt.encode(
        payload={"user_id": int(user_id), "exp": datetime.datetime.now(datetime.UTC) + DEFAULT_EXPIRY},
        key=SECRET_KEY,
        algorithm="HS256",
    )


def decode_token(token: str) -> Snowflake:
    """Decodes a jwt token and returns the stored user id.

    Authors: Christopher

    Parameters
    ----------
    token : str
        The jwt token to decode

    Returns
    -------
    Snowflake
        The user id stored in the jwt token

    Raises
    ------
    jwt.exceptions.PyJWTError
        Raised when either the decoding fails, or there is no user id stored in the jwt.

    """
    payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=("HS256",))
    if user_id := payload.get("user_id"):
        return Snowflake(user_id)
    raise jwt.exceptions.PyJWTError
