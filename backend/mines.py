
import typing
from backend.db.queries import Queries
from backend.internal.ws import GameLobbyBase
from backend.internal.ws import WebsocketClient
from backend.internal.ws import add_event_listener
from shared.models import events


class Mines(GameLobbyBase):
    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)
        self.money = 100

    @add_event_listener(events.UpdateMoney)
    async def update_money_callback(self, event: events.UpdateMoney, _: WebsocketClient) -> None:
        self.money = event.money
        await self.broadcast_event(events.UpdateMoney(money=self.money))

    @add_event_listener(events.ReadyEvent)
    async def on_ready(self, _: events.ReadyEvent, ws: WebsocketClient) -> None:
        await self.send_event(events.UpdateMoney(money=self.money), ws)

    @property
    @typing.override
    def max_num_clients(self) -> int:
        return 1

    @staticmethod
    @typing.override
    def endpoint() -> str:
        return "mines"
