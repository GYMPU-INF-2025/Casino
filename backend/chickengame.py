from websockets import typing
from shared.models import events

from backend.db.queries import Queries
from backend.internal.ws import GameLobbyBase, add_event_listener, WebsocketClient


class Chickengame(GameLobbyBase):
    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)

    @add_event_listener(events.UpdateGamemode)
    async def update_gamemode_callback(self, event: events.UpdateGamemode, _: WebsocketClient) -> None:
        print(f"[Server] Received UpdateGamemode event with mode = {event.gamemode}")
        await self.broadcast_event(events.UpdateGamemode(gamemode=event.gamemode))