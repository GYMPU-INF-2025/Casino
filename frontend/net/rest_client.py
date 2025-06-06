from __future__ import annotations
__all__ = (
    "RestClient",
)

import typing

from frontend.net import routes
from frontend.internal.rest_client import RestClientBase
from shared.models import responses, requests

class RestClient(RestClientBase):

    def __init__(self):
        super().__init__(base_url="http://127.0.0.1:8000/")

    @typing.override
    def login(self, username, password) -> responses.LoginResponse:
        body = requests.LoginRequest(
            username=username,
            password=password
        )
        route = routes.POST_LOGIN.compile()
        return self._perform_request(expected_response=responses.LoginResponse, endpoint=route, data=body)


