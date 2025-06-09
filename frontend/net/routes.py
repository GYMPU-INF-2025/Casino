from __future__ import annotations

import typing

from frontend.internal import Route

GET: typing.Final[str] = "GET"
POST: typing.Final[str] = "POST"
PATCH: typing.Final[str] = "PATCH"
DELETE: typing.Final[str] = "DELETE"
PUT: typing.Final[str] = "PUT"


POST_LOGIN: typing.Final[Route] = Route(POST, "/login")
POST_REGISTER: typing.Final[Route] = Route(POST, "/users")


GET_LOBBYS: typing.Final[Route] = Route(GET, "/{game}")
