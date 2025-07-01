


class AbstractCard:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.next_card = None

    def get_card(self, id: int):
        raise NotImplementedError()

    def add_new_card(self, card):
        if self.next_card is None:
            self.next_card = card
            return
        self.next_card.add_new_card(card)

    def get_length(self, number: int):
        return self.next_card.get_length(number) + 1

class Card(AbstractCard):
    pass

class CardEnding(AbstractCard):
    pass



class CardStack:
    def __init__(self):
        self.begin_card = CardEnding(id=-1, name='last_card')

    def create_card_stack(self):
        for i in range(52):
            new_card = Card(id=i, name="")
            self.begin_card.add_new_card(new_card)

    def get_length_of_cards(self):
        self.begin_card.get_length(self.begin_card.id)




