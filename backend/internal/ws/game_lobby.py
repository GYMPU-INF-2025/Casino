from __future__ import annotations

__all__ = ("EventT", "GameLobbyBase")

import abc
import inspect
import typing

import msgspec
from sanic.log import logger

from shared.internal import Snowflake
from shared.internal.hooks import decode_hook
from shared.internal.hooks import encode_hook
from shared.models import events

EventT = typing.TypeVar("EventT", bound=events.BaseEvent)

if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Coroutine

    from backend.db.models import User
    from backend.db.queries import Queries
    from backend.internal.ws import WebsocketClient
    from shared.models.internal import WebSocketPayload

    CallbackT = Callable[[EventT, WebsocketClient], Coroutine[typing.Any, typing.Any, None]]
    ListenerMapT = dict[str, tuple[type[EventT], list[CallbackT[EventT]]]]


class _GameLobbyMeta(type(abc.ABC)):
    """Metaclass allowing for calling `__post__init__` function after an instance got created.

    Also checks if the provided lobby id is valid.

    Author: Christopher
    """

    @typing.override
    def __call__(cls, *, lobby_id: str, queries: Queries) -> object:
        if not (len(lobby_id) == 5 and lobby_id.isalnum() and lobby_id.upper() == lobby_id):  # noqa: PLR2004
            raise RuntimeError("Invalid lobby-id!")
        obj = super().__call__(lobby_id=lobby_id, queries=queries)
        obj.__post__init__()
        return obj


class GameLobbyBase(abc.ABC, metaclass=_GameLobbyMeta):
    """Base class for every game lobby, handling all the websocket logic.

    To handle all the websocket logic this base class stores all the different connected clients, and every
    registered event callback.

    Authors: Christopher
    """

    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        self._lobby_id: str = lobby_id
        self._queries: Queries = queries
        self._clients: dict[Snowflake, WebsocketClient] = {}
        self._events: ListenerMapT[events.BaseEvent] = {}

    async def get_user_by_client(self, client: Snowflake | WebsocketClient) -> User:
        """Gets a user from the db by their websocket client.

        Authors: Christopher
        """
        if isinstance(client, Snowflake):
            user = await self.queries.get_user_by_id(id_=self._clients[client].user_id)
        else:
            user = await self.queries.get_user_by_id(id_=client.user_id)
        if user is None:
            raise ValueError("User not found")
        return user

    def __post__init__(self) -> None:
        """Function called after an instance of this object was created.

        This is used to scan for event callbacks that are registered with the `add_event_callback` decorator.

        Authors: Christopher
        """
        for attr_name in dir(self):
            maybe_listener = getattr(self, attr_name)

            if callable(maybe_listener) and hasattr(maybe_listener, "__event_type__"):
                self.add_event_callback(maybe_listener.__event_type__, maybe_listener)  # type: ignore[reportArgumentType]

    async def broadcast_event(self, event: events.BaseEvent) -> None:
        """Function that sends an event to every connected client.

        Authors: Christopher
        """
        event_name = event.event_name()
        data = msgspec.to_builtins(event, enc_hook=encode_hook)
        for client in self._clients.values():
            await client.dispatch_event(data, event_name)

    async def send_event(self, event: events.BaseEvent, ws: WebsocketClient) -> None:
        """Function that sends an event to one specified client.

        Authors: Christopher
        """
        event_name = event.event_name()
        data = msgspec.to_builtins(event, enc_hook=encode_hook)
        await ws.dispatch_event(data, event_name)

    def add_event_callback(self, event_type: type[typing.Any], callback: CallbackT[typing.Any]) -> None:
        """Function that adds a function as a callback for a specific event.

        Authors: Christopher
        """
        origin_type = event_type
        if (_origin_type := typing.get_origin(event_type)) is not None:
            origin_type = _origin_type

        try:
            is_event = issubclass(origin_type, events.BaseEvent)
        except TypeError:
            is_event = False

        if not is_event:
            msg = "'event_type' is a non-Event type"
            raise TypeError(msg)

        logger.debug(
            "subscribing callback 'async def %s%s' to event-type %s.%s",
            getattr(callback, "__name__", "<anon>"),
            inspect.signature(callback),
            event_type.__module__,
            event_type.__qualname__,
        )

        if event := self._events.get(event_type.event_name()):
            event[1].append(callback)
            self._events[event_type.event_name()] = event
        else:
            self._events[event_type.event_name()] = (event_type, [callback])

    def set_client(self, user_id: Snowflake, client: WebsocketClient) -> WebsocketClient:
        """Adds a client to the lobby and if the lobby is full it errors.

        Authors: Christopher
        """
        if not self._clients.get(user_id) and self.is_full:
            raise OverflowError("Lobby is full!")
        logger.debug(f"Added client with user id {user_id} and client_id {client.client_id} to lobby {self._lobby_id}")
        self._clients[user_id] = client
        return client

    def get_client(self, user_id: Snowflake) -> WebsocketClient | None:
        return self._clients.get(user_id)

    async def _remove_client(self, user_id: Snowflake) -> None:
        """Removes a client from the lobby and dispatches a LeaveEvent for the client.

        Authors: Christopher
        """
        client = self._clients.pop(user_id, None)
        if client is not None:
            logger.debug(
                f"Removed client with user id {user_id} and client_id {client.client_id} from lobby {self._lobby_id}"
            )
            if not (event := self._events.get(events.LeaveEvent.event_name())):
                return
            for callback in event[1]:
                try:
                    await callback(events.LeaveEvent(), client)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Exception occurred when handling LEAVE event", exc_info=exc)
        else:
            logger.debug("Tried removing client with user id %s but was not found!", user_id)

    @property
    def queries(self) -> Queries:
        return self._queries

    @staticmethod
    @abc.abstractmethod
    def endpoint() -> str:
        """Returns the endpoint name."""

    @property
    @abc.abstractmethod
    def max_num_clients(self) -> int:
        """Returns the maximum amount of clients that can be in the lobby."""

    @property
    def num_clients(self) -> int:
        return len(self._clients)

    @property
    def is_full(self) -> bool:
        return self.num_clients >= self.max_num_clients

    async def __handle_dispatch(self, payload: WebSocketPayload, client: WebsocketClient) -> None:
        """Internal function that handles event dispatches.

        Authors: Christopher
        """
        if not payload.t or not (event := self._events.get(payload.t)):
            return
        event_obj = msgspec.convert(payload.d, type=event[0], dec_hook=decode_hook)
        for callback in event[1]:
            try:
                await callback(event_obj, client)
            except Exception as exc:  # noqa: BLE001
                logger.exception(f"Exception occurred when handling event {payload.t}", exc_info=exc)

    async def send_ready(self, user: User) -> None:
        """Function that sends the ready event for a specific user."""
        client = self.get_client(user.id)
        if client is None:
            return
        event_obj = await client.send_ready(user=user, num_clients=self.num_clients)
        if not (event := self._events.get(events.ReadyEvent.event_name())):
            return
        for callback in event[1]:
            try:
                await callback(event_obj, client)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Exception occurred when handling READY event", exc_info=exc)

    async def handle_ws(self, user_id: Snowflake) -> None:
        client = self.get_client(user_id)
        if client is None:
            return
        await client.handle_ws(self.__handle_dispatch, self._remove_client)
