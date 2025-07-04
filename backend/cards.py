import random
import abc

class AbstractCard(abc.ABC):
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.next_card = None

    def get_length(self, number: int):
        if self.next_card is None:
            return 0
        return self.next_card.get_length(number) + 1

    @abc.abstractmethod
    def set_position(self, current_position: int, new_position: int, card):
        raise NotImplementedError()

class Card(AbstractCard):
    def set_position(self, current_position: int, new_position: int, card: AbstractCard):
       if current_position == new_position:
           new_card = Card(card.id, card.name)
           new_card.next_card = self.next_card
           self.next_card = new_card
           return
       self.next_card.set_position(current_position+1, new_position, card)



class CardEnding(AbstractCard):
    def set_position(self, current_position: int, new_position: int, card: AbstractCard):
        pass



class CardStack:
    """
    Implementierung des Kartenstapples basierend auf dem Kompositium
    Zum Benutzen:
    Objekt erstellen und give_card() aufrufen.

    Authors: Quirin
    """


    def __init__(self):
        self.begin_card = CardEnding(id=-1, name='last_card')
        self.create_card_stack()
        self.num_of_cards = self.get_length_of_cards()
        self.shuffle()

    def create_card_stack(self):
        for i in range(52):
            new_card = Card(id=i, name=card_names[i])
            new_card.next_card = self.begin_card
            self.begin_card = new_card

    def shuffle(self):
        for i in range(self.num_of_cards*2):
            new_position = random.randint(1, self.num_of_cards-1)
            self.begin_card.set_position(0, new_position, self.begin_card)
            self.begin_card = self.begin_card.next_card

    def give_card(self):
        card = {'id': self.begin_card.id, 'name': self.begin_card.name}
        self.begin_card = self.begin_card.next_card
        return card


    def get_length_of_cards(self) -> int:
        self.num_of_cards = self.begin_card.get_length(-1)
        return self.num_of_cards


card_names = [
    "cardClubsA", "cardClubs2", "cardClubs3", "cardClubs4", "cardClubs5",
    "cardClubs6", "cardClubs7", "cardClubs8", "cardClubs9", "cardClubs10",
    "cardClubsJ", "cardClubsQ", "cardClubsK",
    "cardDiamondsA", "cardDiamonds2", "cardDiamonds3", "cardDiamonds4", "cardDiamonds5",
    "cardDiamonds6", "cardDiamonds7", "cardDiamonds8", "cardDiamonds9", "cardDiamonds10",
    "cardDiamondsJ", "cardDiamondsQ", "cardDiamondsK",
    "cardHeartsA", "cardHearts2", "cardHearts3", "cardHearts4", "cardHearts5",
    "cardHearts6", "cardHearts7", "cardHearts8", "cardHearts9", "cardHearts10",
    "cardHeartsJ", "cardHeartsQ", "cardHeartsK",
    "cardSpadesA", "cardSpades2", "cardSpades3", "cardSpades4", "cardSpades5",
    "cardSpades6", "cardSpades7", "cardSpades8", "cardSpades9", "cardSpades10",
    "cardSpadesJ", "cardSpadesQ", "cardSpadesK"
]

