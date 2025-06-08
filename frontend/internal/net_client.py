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
    
    def login(self, username: str, password: str) -> None:
        response = self._rest_client.login(username=username, password=password)
        self.set_token(token=response.token)

    def register(self, username: str, password: str) -> None:
        response = self._rest_client.register(username=username, password=password)
    
    @property
    def rest(self) -> RestClientT:
        return self._rest_client
