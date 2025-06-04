import http

import httpx
import msgspec.json

from shared.internal.hooks import decode_hook
from shared.models import ErrorResponse

__all__ = (
    "HTTPError",
    "HTTPResponseError",
    "ClientHTTPError",
    "InternalServerError",
    "generate_error"
)

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

    def __init__(self, url: str, status: http.HTTPStatus | int, headers: httpx.Headers, raw_body: bytes, name: str, message: str, detail: str) -> None:
        self.url = url
        self.status = status
        self.headers = headers
        self.raw_body = raw_body
        self.name = name
        self.message = message
        self.detail = detail

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
        return ClientHTTPError(url=url, status=status, headers=response.headers, raw_body=raw_body, name=body.name, message=body.message, detail=body.detail)
    if 500 <= status < 600:
        return InternalServerError(url=url, status=status, headers=response.headers, raw_body=raw_body, name=body.name, message=body.message, detail=body.detail)
    return HTTPResponseError(url=url, status=status, headers=response.headers, raw_body=raw_body, name=body.name, message=body.message, detail=body.detail)
