from __future__ import annotations

__all__ = ("RestClientBase",)

import http
import sys
import typing

import httpx
import msgspec

from frontend.internal import CompiledRoute
from shared.internal.hooks import encode_hook, decode_hook

_AUTHORIZATION_HEADER: typing.Final[str] = sys.intern("Authorization")
_CONTENT_HEADER: typing.Final[str] = sys.intern("Content-Type")

_APPLICATION_JSON: typing.Final[str] = sys.intern("application/json")


T = typing.TypeVar("T",bound=msgspec.Struct | None)

class RestClientBase:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self._token: str | None = token
        self._base_url: str = base_url
        self._client = httpx.Client(auth=self.__auth_flow, base_url=self._base_url)

    def __auth_flow(self, request: httpx.Request) -> httpx.Request:
        if self._token:
            request.headers[_AUTHORIZATION_HEADER] = f"Token {self._token}"
        return request

    def set_token(self, token: str | None) -> None:
        self._token = token

    def login(self, username: str, password: str) -> None:
        return

    def _perform_request(self, expected_response: type[T], endpoint: CompiledRoute, *, data: dict[str, typing.Any] | None = None) -> T:
        content = msgspec.json.encode(data, enc_hook=encode_hook)
        response = self._client.request(method=endpoint.method, url=endpoint.compiled_path, content=content)

        if response.status_code == http.HTTPStatus.NO_CONTENT and expected_response is None:
            return None

        if 200 <= response.status_code < 300:
            if (content_type := response.headers.get(_CONTENT_HEADER)) == _APPLICATION_JSON:
                return msgspec.json.decode(response.content, type=expected_response, dec_hook=decode_hook)

            real_url = str(response.url)
            msg = f"Expected JSON [{content_type=}, {real_url=}]"
            
        raise Exception
