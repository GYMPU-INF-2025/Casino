from __future__ import annotations
__all__ = (
    "RestClient",
)

from frontend.internal.rest_client import RestClientBase

class RestClient(RestClientBase):


    def __init__(self):
        super().__init__(base_url="http://127.0.0.1:8000/")
