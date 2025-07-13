from __future__ import annotations

import http
import typing

import msgspec.json

from shared.internal.hooks import decode_hook
from shared.models import ErrorResponse

if typing.TYPE_CHECKING:
    import httpx

__all__ = ("ClientHTTPError", "HTTPError", "HTTPResponseError", "InternalServerError", "generate_error")


"""Different classes that represent http/network erros.

Authors: Christopher
"""


class HTTPError(RuntimeError):
    """"""


class HTTPResponseError(HTTPError):
    url: str
    status: http.HTTPStatus | int
    headers: httpx.Headers
    raw_body: bytes

    name: str
    message: str
    detail: str

    def __init__(
        self,
        url: str,
        status: http.HTTPStatus | int,
        headers: httpx.Headers,
        raw_body: bytes,
        name: str,
        message: str,
        detail: str,
    ) -> None:
        self.url = url
        self.status = status
        self.headers = headers
        self.raw_body = raw_body
        self.name = name
        self.message = message
        self.detail = detail

    @typing.override
    def __str__(self) -> str:
        if isinstance(self.status, http.HTTPStatus):
            name = self.status.name.replace("_", " ").title()
            name_value = f"{name} {self.status.value}"

        else:
            name_value = f"Unknown Status {self.status}"

        code_str = f" ({self.status})" if self.status else ""

        if self.message:
            body = f"{self.message}: {self.detail}"
        else:
            try:
                body = self.raw_body.decode("utf-8")
            except (AttributeError, UnicodeDecodeError, TypeError, ValueError):
                body = str(self.raw_body)

        chomped = len(body) > 200

        return f"{name_value}:{code_str} '{body[:200]}{'...' if chomped else ''}' for {self.url}"


class ClientHTTPError(HTTPResponseError):
    """"""


class InternalServerError(HTTPResponseError):
    """"""


error_decoder = msgspec.json.Decoder(ErrorResponse, dec_hook=decode_hook)


def generate_error(response: httpx.Response) -> HTTPResponseError:
    url = str(response.url)
    raw_body = response.content

    body = error_decoder.decode(raw_body)

    try:
        status: http.HTTPStatus | int = http.HTTPStatus(response.status_code)
    except ValueError:
        status = response.status_code

    if 400 <= status < 500:
        return ClientHTTPError(
            url=url,
            status=status,
            headers=response.headers,
            raw_body=raw_body,
            name=body.name,
            message=body.message,
            detail=body.detail,
        )
    if 500 <= status < 600:
        return InternalServerError(
            url=url,
            status=status,
            headers=response.headers,
            raw_body=raw_body,
            name=body.name,
            message=body.message,
            detail=body.detail,
        )
    return HTTPResponseError(
        url=url,
        status=status,
        headers=response.headers,
        raw_body=raw_body,
        name=body.name,
        message=body.message,
        detail=body.detail,
    )
