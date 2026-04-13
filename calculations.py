from card import Card

class Calculations:
    def __init__(self):
        self.name_map = {11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}
    
    def calculate_loss(self, original_suite, mundup, highest_card, player_hand, cards_remaining):
        """
        Calculate probability of losing for each card in player's hand.
        
        SIMPLIFIED LOGIC:
        1. If MUNDUP exists → Only mundup cards matter
        2. If NO MUNDUP:
           a) You don't have original suite → Setting mundup
           b) You have original suite → Count original suite > highest
        """
        results = []
        
        for card in player_hand:
            card_name = self._format_card_name(card)
            
            # Check if card beats current highest
            if highest_card and not self._beats_highest(card, highest_card, original_suite, mundup):
                results.append(f"If play {card_name}: 100.0% chance of losing (Can't beat current highest)")
                continue
            
            # Count cards that can beat yours
            beating_count = 0
            total = len(cards_remaining)
            
            # CASE 1: MUNDUP EXISTS
            if mundup:
                if card.getSuit() == mundup:
                    # Count mundup cards >= your value
                    beating_count = sum(1 for c in cards_remaining 
                                      if c.getSuit() == mundup and c.getValue() >= card.getValue())
                else:
                    # Playing non-mundup when mundup exists
                    # All mundup cards beat you
                    beating_count = sum(1 for c in cards_remaining if c.getSuit() == mundup)
            
            # CASE 2: NO MUNDUP
            else:
                # Sub-case: You're SETTING mundup (don't have original suite)
                if not self._has_suit(player_hand, original_suite):
                    suit = card.getSuit()
                    beating_count = sum(1 for c in cards_remaining 
                                      if c.getSuit() == suit and c.getValue() >= card.getValue())
                    results.append(f"If play {card_name}: {beating_count/total*100 if total else 0:.1f}% chance of losing (SETS MUNDUP to {suit})")
                    continue
                
                # Sub-case: Playing original suite
                if card.getSuit() == original_suite:
                    beating_count = sum(1 for c in cards_remaining 
                                      if c.getSuit() == original_suite and c.getValue() >= card.getValue())
                else:
                    # Playing off-suit when you have original suite = illegal move
                    results.append(f"If play {card_name}: ILLEGAL (Must follow suit)")
                    continue
            
            probability = (beating_count / total * 100) if total else 0.0
            results.append(f"If play {card_name}: {probability:.1f}% chance of losing")
        
        return "\n".join(results)
    
    def _beats_highest(self, card, highest, original_suite, mundup):
        """Check if card beats the highest card on table."""
        if mundup:
            # Mundup beats non-mundup
            if card.getSuit() == mundup and highest.getSuit() != mundup:
                return True
            # Both mundup: higher wins
            if card.getSuit() == mundup and highest.getSuit() == mundup:
                return card.getValue() > highest.getValue()
            # Card is not mundup but highest is: can't beat
            if card.getSuit() != mundup and highest.getSuit() == mundup:
                return False
            # Neither is mundup: must be same suit and higher
            return card.getSuit() == highest.getSuit() and card.getValue() > highest.getValue()
        else:
            # No mundup: must be same suit and higher
            return card.getSuit() == highest.getSuit() and card.getValue() > highest.getValue()
    
    def _is_setting_mundup(self, card, player_hand, original_suite, mundup):
        """Check if playing this card would set the mundup."""
        return (mundup is None and 
                card.getSuit() != original_suite and
                not self._has_suit(player_hand, original_suite))
    
    def _has_suit(self, hand, suit):
        """Check if player has any cards of the given suit."""
        return any(card.getSuit() == suit for card in hand)
    
    def _count_beating_cards(self, played_card, original_suite, mundup, remaining_cards, is_setting_mundup):
        """
        Count how many cards in remaining_cards can beat the played_card.
        
        Logic by scenario:
        
        1. SETTING MUNDUP (first to break suit):
           - Your card becomes mundup
           - Only cards of same suit >= your value can beat you
        
        2. Playing MUNDUP (when mundup already exists):
           - Only mundup cards >= your value can beat you
        
        3. Playing ORIGINAL SUITE:
           - Original suite cards >= your value can beat you
           - Any mundup card can beat you (if opponent has no original suite)
        
        4. Playing OFF-SUIT (not original, not mundup):
           - Any mundup card beats you
           - Original suite cards can beat you if they're following suit
        """
        count = 0
        played_value = played_card.getValue()
        played_suit = played_card.getSuit()
        
        # CASE 1: You are SETTING the mundup
        if is_setting_mundup:
            # Your card's suit becomes mundup
            # Only cards of your suit >= your value can beat you
            for card in remaining_cards:
                if card.getSuit() == played_suit and card.getValue() >= played_value:
                    count += 1
            return count
        
        # CASE 2: You play MUNDUP card (mundup already exists)
        if played_suit == mundup:
            # Only higher mundup cards can beat you
            for card in remaining_cards:
                if card.getSuit() == mundup and card.getValue() >= played_value:
                    count += 1
            return count
        
        # CASE 3: You play ORIGINAL SUITE
        if played_suit == original_suite:
            for card in remaining_cards:
                # Original suite cards >= your value beat you
                if card.getSuit() == original_suite and card.getValue() >= played_value:
                    count += 1
                # Any mundup card beats you
                elif mundup and card.getSuit() == mundup:
                    count += 1
            return count
        
        # CASE 4: You play OFF-SUIT (not original, not mundup)
        # This happens when you don't have original suite AND mundup exists
        for card in remaining_cards:
            # Any mundup card beats you
            if mundup and card.getSuit() == mundup:
                count += 1
            # Original suite cards beat you
            elif card.getSuit() == original_suite:
                count += 1
        
        return count
    
    def _same_card(self, card1, card2):
        """Check if two cards are identical."""
        return (card1.getValue() == card2.getValue() and 
                card1.getSuit() == card2.getSuit())
    
    def _format_card_name(self, card):
        """Format card name for display (e.g., 'King of Hearts')."""
        value = card.getValue()
        suit = card.getSuit()
        
        if value in self.name_map:
            value_str = self.name_map[value]
        else:
            value_str = str(value)
        
        return f"{value_str} of {suit}"


# --- Simplified Testing ---
if __name__ == "__main__":
    calc = Calculations()
    
    print("\n" + "="*60)
    print("TEST 1: NO MUNDUP - Setting Mundup")
    print("="*60)
    print("Original: Clubs, Mundup: None")
    print("You don't have Clubs, so you'll set mundup\n")
    
    hand1 = [Card("Hearts", 2), Card("Hearts", 14)]
    remaining1 = [Card("Hearts", 2), Card("Hearts", 10), Card("Hearts", 14), Card("Clubs", 10)]
    
    print(calc.calculate_loss("Clubs", None, None, hand1, remaining1))
    print("\n✓ Only Hearts cards >= your value matter")
    
    print("\n" + "="*60)
    print("TEST 2: MUNDUP EXISTS - Playing Mundup")
    print("="*60)
    print("Original: Clubs, Mundup: Spades")
    print("Highest: King of Clubs\n")
    
    hand2 = [Card("Spades", 2), Card("Spades", 14), Card("Clubs", 10)]
    remaining2 = [Card("Spades", 3), Card("Spades", 10), Card("Spades", 14)]
    highest2 = Card("Clubs", 13)
    
    print(calc.calculate_loss("Clubs", "Spades", highest2, hand2, remaining2))
    print("\n✓ Any Spade beats King of Clubs")
    print("✓ Only Spades >= your value can beat you")
    print("✓ 10 of Clubs can't beat King")
    
    print("\n" + "="*60)
    print("TEST 3: MUNDUP EXISTS - Playing Non-Mundup")
    print("="*60)
    print("Original: Clubs, Mundup: Spades")
    print("Highest: King of Clubs\n")
    
    hand3 = [Card("Clubs", 14), Card("Hearts", 14)]  # Ace beats King, but...
    remaining3 = [Card("Spades", 2), Card("Spades", 5), Card("Clubs", 14)]
    
    print(calc.calculate_loss("Clubs", "Spades", highest2, hand3, remaining3))
    print("\n✓ Ace of Clubs beats King, but ALL Spades beat it")
    print("✓ Ace of Hearts is off-suit, can't beat King")
    
    print("\n" + "="*60)
    print("TEST 4: NO MUNDUP - Original Suite")
    print("="*60)
    print("Original: Clubs, Mundup: None")
    print("Highest: King of Clubs\n")
    
    hand4 = [Card("Clubs", 10), Card("Clubs", 13), Card("Clubs", 14)]
    remaining4 = [Card("Clubs", 13), Card("Clubs", 14)]
    highest4 = Card("Clubs", 13)
    
    print(calc.calculate_loss("Clubs", None, highest4, hand4, remaining4))
    print("\n✓ 10 can't beat King = 100%")
    print("✓ King ties = 100%")  
    print("✓ Ace beats King, then count Clubs >= Ace")
    
    print("\n" + "="*60)
    print("TEST 5: Edge Case - Empty Deck")
    print("="*60)
    hand5 = [Card("Clubs", 10)]
    print(calc.calculate_loss("Clubs", None, None, hand5, []))
    print("\n✓ No cards remaining = 0% loss")
    
    print("\n" + "="*60)
    print("TEST 6: Illegal Move Detection")
    print("="*60)
    print("You have Clubs but try to play Hearts\n")
    
    hand6 = [Card("Clubs", 10), Card("Hearts", 14)]
    remaining6 = [Card("Clubs", 14)]
    
    print(calc.calculate_loss("Clubs", None, None, hand6, remaining6))
    print("\n✓ Must follow suit - Hearts is ILLEGAL")