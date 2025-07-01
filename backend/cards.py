import random


class AbstractCard:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.next_card = None

    def get_card(self, id_: int):
        raise NotImplementedError()

    def add_new_card(self, card):
        if self.next_card is None:
            self.next_card = card
            return
        self.next_card.add_new_card(card)

    def get_length(self, number: int):
        if self.next_card is None:
            return 0
        return self.next_card.get_length(number) + 1

    def set_position(self, current_position: int, new_position: int, card):
        raise NotImplementedError()

class Card(AbstractCard):
    def set_position(self, current_position: int, new_position: int, card: AbstractCard):
        if current_position == new_position:
            card.next_card = self.next_card
            self.next_card = card
            return
        self.next_card.set_position(current_position+1, new_position, card)

    def get_card(self, id_: int):
        if id_ == self.id:
            self.next_card = self.next_card.next_card
            return self.next_card
        return self.next_card.get_card(id_)



class CardEnding(AbstractCard):
    def set_position(self, current_position: int, new_position: int, card: AbstractCard):
        pass

    def get_card(self, id_: int):
        pass



class CardStack:
    def __init__(self):
        self.begin_card = CardEnding(id=-1, name='last_card')
        self.create_card_stack()
        self.num_of_cards = self.get_length_of_cards()

    def create_card_stack(self):
        for i in range(5):
            new_card = Card(id=i, name="")
            self.begin_card.add_new_card(new_card)

    def shuffle(self):
        for i in range(2):
            card_id = random.randint(0, self.num_of_cards-1)
            card = self.begin_card.get_card(card_id)

            new_position = random.randint(0, self.num_of_cards-1)
            self.begin_card.set_position(current_position=0, new_position=new_position, card=card)

            print(f"{card_id} {new_position}")


    def get_length_of_cards(self) -> int:
        self.num_of_cards = self.begin_card.get_length(-1)
        return self.num_of_cards




