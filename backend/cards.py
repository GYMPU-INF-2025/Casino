from __future__ import annotations

import abc
import random
import typing

import msgspec


class CardValue(msgspec.Struct):
    """Class holding data for each card."""

    id: int
    name: str


class AbstractCard(abc.ABC):
    """Abstract base class for the cards in the `CardStack`.

    Authors: Quirin
    """

    def __init__(self, id_: int, name: str) -> None:
        self.value = CardValue(id=id_, name=name)
        self.next_card: AbstractCard | None = None

    def get_length(self, number: int) -> int:
        if self.next_card is None:
            return 0
        return self.next_card.get_length(number) + 1

    @abc.abstractmethod
    def set_position(self, current_position: int, new_position: int, card: AbstractCard) -> None: ...


class Card(AbstractCard):
    """Card representing a playable card in the stack."""

    def __init__(self, id_: int, name: str, next_card: AbstractCard) -> None:
        self.value = CardValue(id=id_, name=name)
        self.next_card: AbstractCard = next_card

    @typing.override
    def set_position(self, current_position: int, new_position: int, card: AbstractCard) -> None:
        if current_position == new_position:
            self.next_card = Card(card.value.id, card.value.name, self.next_card)  # type: ignore[reportIncompatibleVariableOverride]
            return
        self.next_card.set_position(current_position + 1, new_position, card)


class CardEnding(AbstractCard):
    """Card representing the end of the stack."""

    @typing.override
    def set_position(self, current_position: int, new_position: int, card: AbstractCard) -> None:
        pass


class CardStack:
    """Implementation of the card stack based on the composite pattern.
    Usage:
    Create an object and call give_card().

    Authors: Quirin
    """

    def __init__(self) -> None:
        self.begin_card: AbstractCard = CardEnding(id_=-1, name="last_card")
        self.__create_card_stack()
        self.num_of_cards = self.get_length_of_cards()
        self.shuffle()

    def __create_card_stack(self) -> None:
        """Internal method used to create 52 cards."""
        for i in range(52):
            new_card = Card(id_=i, name=card_names[i], next_card=self.begin_card)
            self.begin_card = new_card

    def recreate_card_stack(self) -> None:
        """Method used to recreate the card stack."""
        self.begin_card = CardEnding(id_=-1, name="last_card")
        self.__create_card_stack()
        self.get_length_of_cards()
        self.shuffle()

    def shuffle(self) -> None:
        """Method used to shuffle the card stack. This method does not add missing cards!"""
        for _ in range(self.get_length_of_cards() * 2):
            new_position = random.randint(1, self.num_of_cards - 1)
            if not isinstance(self.begin_card, Card):
                break
            self.begin_card.set_position(0, new_position, self.begin_card)
            self.begin_card = self.begin_card.next_card

    def give_card(self) -> CardValue:
        """Returns the card from the top of the stack.

        Raises
        ------
        ValueError
            Raised when the stack is empty.
        """
        card = self.begin_card
        if not isinstance(card, Card):
            raise ValueError("CardStack is empty")  # noqa: TRY004
        self.begin_card = card.next_card
        return card.value

    def get_length_of_cards(self) -> int:
        """Returns the number of cards in the stack."""
        self.num_of_cards = self.begin_card.get_length(-1)
        return self.num_of_cards


card_names = [
    "cardClubsA",
    "cardClubs2",
    "cardClubs3",
    "cardClubs4",
    "cardClubs5",
    "cardClubs6",
    "cardClubs7",
    "cardClubs8",
    "cardClubs9",
    "cardClubs10",
    "cardClubsJ",
    "cardClubsQ",
    "cardClubsK",
    "cardDiamondsA",
    "cardDiamonds2",
    "cardDiamonds3",
    "cardDiamonds4",
    "cardDiamonds5",
    "cardDiamonds6",
    "cardDiamonds7",
    "cardDiamonds8",
    "cardDiamonds9",
    "cardDiamonds10",
    "cardDiamondsJ",
    "cardDiamondsQ",
    "cardDiamondsK",
    "cardHeartsA",
    "cardHearts2",
    "cardHearts3",
    "cardHearts4",
    "cardHearts5",
    "cardHearts6",
    "cardHearts7",
    "cardHearts8",
    "cardHearts9",
    "cardHearts10",
    "cardHeartsJ",
    "cardHeartsQ",
    "cardHeartsK",
    "cardSpadesA",
    "cardSpades2",
    "cardSpades3",
    "cardSpades4",
    "cardSpades5",
    "cardSpades6",
    "cardSpades7",
    "cardSpades8",
    "cardSpades9",
    "cardSpades10",
    "cardSpadesJ",
    "cardSpadesQ",
    "cardSpadesK",
]
