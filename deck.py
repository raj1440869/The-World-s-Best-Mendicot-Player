import random
from card import Card

class Deck:
    def __init__(self):
        self.cards = []
        suits = ["Clubs", "Diamonds", "Hearts", "Spades"]
        
        # 1. Define the name map at the class level or in init so all functions can use it
        self.name_map = {11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}
        
        for suit in suits:
            for _ in range(2):
                suit_row = [] 
                for value in range(2, 15):
                    new_card = Card(suit, value)
                    new_card.count = 1 
                    suit_row.append(new_card)
                self.cards.append(suit_row)
        
        self.suit_map = {
            "Clubs": [0, 1], 
            "Diamonds": [2, 3], 
            "Hearts": [4, 5], 
            "Spades": [6, 7]
        }

    def _get_display_name(self, val):
        """Helper to convert 14 -> Ace, 11 -> Jack, etc."""
        if val in self.name_map:
            return self.name_map[val]
        return str(val)

    def dealRandomCard(self):
        """
        Removes and returns a random card from the deck.
        Returns None if deck is empty.
        """
        # Flatten all cards into a single list
        all_cards = []
        for suit_row in self.cards:
            all_cards.extend(suit_row)
        
        # If deck is empty, return None
        if len(all_cards) == 0:
            return None
        
        # Pick a random card
        random_card = random.choice(all_cards)
        
        # Remove it from the deck
        for suit_row in self.cards:
            if random_card in suit_row:
                suit_row.remove(random_card)
                break
        
        return random_card

    def removeCard(self, suit, value):
        target_card = Card(suit, value)
        target_val = target_card.getValue()
        target_suit = target_card.getSuit()

        if target_suit in self.suit_map:
            row_indices = self.suit_map[target_suit]
            
            for row_index in row_indices:
                suit_row = self.cards[row_index]
                
                for card in suit_row:
                    if card.getValue() == target_val:
                        suit_row.remove(card)
                        
                        # --- UPDATED PRINT LOGIC ---
                        display_name = self._get_display_name(target_val)
                        print(f"Removed: {display_name} of {target_suit} (from Row {row_index})")
                        
                        return 
            
        print(f"Card not found: {value} of {suit}")

    def toString(self):
        for i, suit_row in enumerate(self.cards):
            if not suit_row: continue 

            current_suit = suit_row[0].getSuit()
            display_values = []

            for card in suit_row:
                val = card.getValue()
                # Use the same helper for consistency
                display_values.append(self._get_display_name(val))
            
            print(f"{current_suit} (Row {i}): {','.join(display_values)}")

    def cardsLeft(self):
        total_count = 0
        for suit_row in self.cards:
            for card in suit_row:
                total_count += card.getCount()     
        return total_count

# --- Test Run ---
if __name__ == "__main__":
    deck = Deck()
    print("\n--- Removing Cards ---")
    deck.removeCard("Clubs", 14) 
    deck.removeCard("Hearts", "Jack") 
    deck.removeCard("Spades", 13)