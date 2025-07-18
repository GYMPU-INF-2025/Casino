from __future__ import annotations

__all__ = ("RestClientBase",)

import abc
import collections.abc
import http
import sys
import typing

import httpx
import msgspec

from frontend.net import HTTPError
from frontend.net import generate_error
from shared.internal.hooks import decode_hook
from shared.internal.hooks import encode_hook

if typing.TYPE_CHECKING:
    from frontend.internal import CompiledRoute
    from shared.models import responses


_AUTHORIZATION_HEADER: typing.Final[str] = sys.intern("Authorization")
_CONTENT_HEADER: typing.Final[str] = sys.intern("Content-Type")

_APPLICATION_JSON: typing.Final[str] = sys.intern("application/json")


T = typing.TypeVar("T", bound=msgspec.Struct | collections.abc.Sequence[msgspec.Struct] | None)


class RestClientBase(abc.ABC):
    """Abstract base class for the rest client.

    Contains logic used to execute requests, manages authentication
    and predefines required rest methods.

    Authors: Christopher
    """

    def __init__(self, base_url: str, token: str | None = None) -> None:
        self._token: str | None = token
        self._base_url: str = base_url
        self._client = httpx.Client(auth=self.__auth_flow, base_url=self._base_url)
        self._json_encoder = msgspec.json.Encoder(enc_hook=encode_hook)

    def __auth_flow(self, request: httpx.Request) -> httpx.Request:
        """Internal method passed to the `httpx.Client`.

        If there is a token set, an authorization header will be added.

        Authors: Christopher
        """
        if self._token:
            request.headers[_AUTHORIZATION_HEADER] = f"Bearer {self._token}"
        return request

    def set_token(self, token: str | None) -> None:
        self._token = token

    def _perform_request(
        self,
        expected_response: type[T],
        endpoint: CompiledRoute,
        *,
        data: dict[str, typing.Any] | msgspec.Struct | None = None,
    ) -> T:
        """Execute a request.

        Parameters
        ----------
        expected_response: type[T]
            The type of the returned object. This has to be either a `msgspec.Struct`,
            a sequence of `msgspec.Struct` or `None`.
        endpoint: CompiledRoute
            The endpoint that should be requested.
        data: dict[str, typing.Any] | msgspec.Struct | None
            Optional data that should be sent in the request body. Will be formatted to json.

        Raises
        ------
        HTTPError
            Expected response to be json but got some other content type.
        HTTPResponseError
            The server returned a response code that signals that something went wrong.

        Returns
        -------
        T
            The expected object.
        """
        content: bytes | None = None
        if isinstance(data, (dict, msgspec.Struct)):
            content = self._json_encoder.encode(data)
        response = self._client.request(method=endpoint.method, url=endpoint.compiled_path, content=content)

        if response.status_code == http.HTTPStatus.NO_CONTENT and expected_response is type(None):
            return expected_response()  # this returns None but for some reason pyright complains if we do `return None`

        if 200 <= response.status_code < 300:  # noqa: PLR2004
            if (content_type := response.headers.get(_CONTENT_HEADER)) == _APPLICATION_JSON:
                return msgspec.json.decode(response.content, type=expected_response, dec_hook=decode_hook)

            real_url = str(response.url)
            msg = f"Expected JSON [{content_type=}, {real_url=}]"
            raise HTTPError(msg)

        raise generate_error(response)

    @abc.abstractmethod
    def login(self, username: str, password: str) -> responses.LoginResponse: ...
