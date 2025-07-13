from __future__ import annotations

import typing

import msgspec


from shared.models import responses
from shared.internal import snowflakes


class BaseEvent(msgspec.Struct):
    @classmethod
    def event_name(cls) -> str:
        result = []
        for i, char in enumerate(cls.__name__):
            if char.isupper() and i != 0:
                result.append("_")
            result.append(char)
        return "".join(result).upper()

class ReadyEvent(BaseEvent):
    user: responses.PublicUser
    client_id: snowflakes.Snowflake
    num_clients: int

class LeaveEvent(BaseEvent):
    pass

class PrintText(BaseEvent):
    text: str
    text2: str

class UpdateMoney(BaseEvent):
    money: int

class StartSpin(BaseEvent):
    einsatz: int

class kein_Geld(BaseEvent):
    einsatz: int

class Spin_Animation(BaseEvent):
    final_symbols: list[str]

class Money_now(BaseEvent):
     money: int

class Moneyq(BaseEvent):
    einsatz: int


class MinesChangeStake(BaseEvent):
    amount: int

class MinesMineClicked(BaseEvent):
    x: int
    y: int

class MinesMineClickedResponse(BaseEvent):
    x: int
    y: int
    multiplier: float

class MinesGameOver(BaseEvent):
    x: int
    y: int

class MinesRestartGame(BaseEvent):
    pass

class MinesChashout(BaseEvent):
    pass

class MinesChashoutResponse(BaseEvent):
    balance: int

class MinesStartGame(BaseEvent):
    pass

class BlackjackCardData(msgspec.Struct):
    name: str
    value: int

class BlackjackPlayerData(msgspec.Struct):
    username: str
    current_bet: int = msgspec.field(default=0)
    cards: list[BlackjackCardData] = msgspec.field(default_factory=list)

class BlackjackWaitingForBet(BaseEvent):
    wait_time: int

class BlackjackGiveCard(BaseEvent):
    username: str
    card: BlackjackCardData

class BlackjackSetBet(BaseEvent):
    bet: int

class BlackjackUpdateGame(BaseEvent):
    started: bool

    active_players: list[BlackjackPlayerData]
    waiting_players: list[BlackjackPlayerData]

class BlackjackStartGame(BaseEvent):
    pass

class BlackjackHoldCard(BaseEvent):
    pass

class BlackjackDrawCard(BaseEvent):
    pass

class BlackjackDefeat(BaseEvent):
    pass

class BlackjackDraw(BaseEvent):
    pass

class BlackjackWin(BaseEvent):
    pass

class BlackjackPlayerAction(BaseEvent):
    username: str

