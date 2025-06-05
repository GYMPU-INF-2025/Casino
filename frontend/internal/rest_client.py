from __future__ import annotations

__all__ = ("RestClientBase",)

import http
import sys
import typing

import httpx
import msgspec

from frontend.internal import CompiledRoute
from shared.internal.hooks import encode_hook, decode_hook
from frontend.net import generate_error, HTTPError, routes
from shared.models import responses, requests

_AUTHORIZATION_HEADER: typing.Final[str] = sys.intern("Authorization")
_CONTENT_HEADER: typing.Final[str] = sys.intern("Content-Type")

_APPLICATION_JSON: typing.Final[str] = sys.intern("application/json")


T = typing.TypeVar("T",bound=msgspec.Struct | None)

class RestClientBase:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self._token: str | None = token
        self._base_url: str = base_url
        self._client = httpx.Client(auth=self.__auth_flow, base_url=self._base_url)
        self._json_encoder = msgspec.json.Encoder(enc_hook=encode_hook)

    def __auth_flow(self, request: httpx.Request) -> httpx.Request:
        if self._token:
            request.headers[_AUTHORIZATION_HEADER] = f"Token {self._token}"
        return request

    def set_token(self, token: str | None) -> None:
        self._token = token

    def _perform_request(self, expected_response: type[T], endpoint: CompiledRoute, *, data: dict[str, typing.Any] | msgspec.Struct | None = None) -> T:
        content: bytes | None = None
        if isinstance(data, dict) or isinstance(data, msgspec.Struct):
            content = self._json_encoder.encode(data)
        response = self._client.request(method=endpoint.method, url=endpoint.compiled_path, content=content)

        if response.status_code == http.HTTPStatus.NO_CONTENT and expected_response is None:
            return None

        if 200 <= response.status_code < 300:
            if (content_type := response.headers.get(_CONTENT_HEADER)) == _APPLICATION_JSON:
                return msgspec.json.decode(response.content, type=expected_response, dec_hook=decode_hook)

            real_url = str(response.url)
            msg = f"Expected JSON [{content_type=}, {real_url=}]"
            raise HTTPError(msg)
            
        raise generate_error(response)

    def login(self, username: str, password: str) -> responses.LoginResponse:
        body = requests.LoginRequest(
            username=username,
            password=password
        )
        route = routes.POST_LOGIN.compile()
        return self._perform_request(expected_response=responses.LoginResponse, endpoint=route, data=body)
        