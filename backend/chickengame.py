from arcade.gui import events
from websockets import typing

from backend.db.queries import Queries
from backend.internal.ws import GameLobbyBase, add_event_listener, WebsocketClient


class Chickengame(GameLobbyBase):
    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)

'''
    @add_event_listener()
    async def play(self, event: events., _: WebsocketClient) -> None:
'''

