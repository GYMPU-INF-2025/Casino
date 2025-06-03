from __future__ import annotations

__all__ = ("NetClient",)

import typing

from frontend.internal.rest_client import RestClientBase


RestClientT = typing.TypeVar("RestClientT", bound=RestClientBase)

class NetClient(typing.Generic[RestClientT]):
    def __init__(self, rest_client: RestClientT) -> None:
        self._rest_client = rest_client
        self._token: str | None = None

    @property
    def authorized(self) -> bool:
        return self._token is not None

    def set_token(self, token: str | None) -> None:
        self._token = token
        self._rest_client.set_token(token=token)

    def logout(self) -> None:
        self._token = None
    
    @property
    def rest(self) -> RestClientT:
        return self._rest_client
