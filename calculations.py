from card import Card

class Calculations:
    def __init__(self):
        self.name_map = {11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}
    
    def calculate_loss(self, original_suite, mundup, highest_card, player_hand, cards_remaining):
        """
        For each card in player_hand, report either an ILLEGAL flag or the
        probability that some remaining card can beat it.

        Legality rules (Mendicot):
          1. Must follow the led suit if you hold it.
          2. If you can't follow suit but hold trump, you must play trump.
          3. Only if you hold neither may you play anything.

        Threat counting:
          - Playing trump:        only a higher trump beats you.
          - Playing non-trump:    any trump beats you, PLUS any higher
                                  card of the same suit (if no trump is played).
          - Setting trump (first  only higher cards of your chosen suit beat you.
            off-suit play):
          - Ties don't beat you (first-played card wins on equal value).
        """
        results = []

        has_original  = self._has_suit(player_hand, original_suite)
        has_trump     = bool(mundup and self._has_suit(player_hand, mundup))
        total         = len(cards_remaining)

        for card in player_hand:
            card_name = self._format_card_name(card)

            # ── Legality ────────────────────────────────────────────────
            if original_suite:
                if has_original and card.getSuit() != original_suite:
                    results.append(f"If play {card_name}: ILLEGAL (Must follow suit)")
                    continue
                if not has_original and has_trump and card.getSuit() != mundup:
                    results.append(f"If play {card_name}: ILLEGAL (Must play trump)")
                    continue

            # ── Can't beat current highest → certain loss ────────────────
            if highest_card and not self._beats_highest(card, highest_card, original_suite, mundup):
                results.append(f"If play {card_name}: 100.0% chance of losing (Can't beat current highest)")
                continue

            # ── Count remaining cards that would beat this card ──────────
            beating_count = 0

            if mundup:
                if card.getSuit() == mundup:
                    # Only a higher trump beats you
                    beating_count = sum(
                        1 for c in cards_remaining
                        if c.getSuit() == mundup and c.getValue() > card.getValue()
                    )
                else:
                    # Any trump beats you; AND a higher same-suit card beats you
                    # (if every opponent plays same suit and no one plays trump)
                    beating_count = sum(1 for c in cards_remaining if c.getSuit() == mundup)
                    beating_count += sum(
                        1 for c in cards_remaining
                        if c.getSuit() == card.getSuit() and c.getValue() > card.getValue()
                    )
            else:
                if not has_original:
                    # Setting trump: only higher cards of your suit beat you
                    beating_count = sum(
                        1 for c in cards_remaining
                        if c.getSuit() == card.getSuit() and c.getValue() > card.getValue()
                    )
                    pct = beating_count / total * 100 if total else 0.0
                    results.append(
                        f"If play {card_name}: {pct:.1f}% chance of losing "
                        f"(SETS TRUMP to {card.getSuit()})"
                    )
                    continue
                else:
                    # Following suit, no trump: only higher same-suit beats you
                    beating_count = sum(
                        1 for c in cards_remaining
                        if c.getSuit() == original_suite and c.getValue() > card.getValue()
                    )

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
    
    def _has_suit(self, hand, suit):
        """Check if player has any cards of the given suit."""
        return any(card.getSuit() == suit for card in hand)
    
    # ------------------------------------------------------------------
    # Best-move selection
    # ------------------------------------------------------------------

    def best_move(self, original_suite, mundup, highest_card,
                  player_hand, cards_remaining, teammate_winning=False):
        """
        Return the single Card from player_hand that is the mathematically
        best play given current game state.

        Strategy (in priority order):
          1. Leading the trick → lead with an Ace, else highest card of
             the suit we hold the most of (establish strength).
          2. Can't beat current highest → play lowest legal card (minimize waste).
          3. Teammate is currently winning → play lowest legal card (don't steal).
          4. Can beat → play the LOWEST card that still beats the highest
             (win as cheaply as possible, preserve big cards).
        """
        if not player_hand:
            return None

        legal = self._legal_cards(original_suite, mundup, player_hand)

        # Leading the trick
        if not original_suite or highest_card is None:
            return self._best_lead(legal, cards_remaining, mundup)

        # Cards that can beat the current highest
        beating = [c for c in legal
                   if self._beats_highest(c, highest_card, original_suite, mundup)]

        # Can't beat anything → play lowest legal card
        if not beating:
            return min(legal, key=lambda c: c.getValue())

        # Teammate winning → don't steal the trick
        if teammate_winning:
            return min(legal, key=lambda c: c.getValue())

        # Win cheaply → lowest card that still beats current highest
        return min(beating, key=lambda c: c.getValue())

    def _legal_cards(self, original_suite, mundup, player_hand):
        """
        Return the subset of player_hand that is legal to play.

        Rules (in priority order):
          1. Must follow the led suit if held.
          2. Must play trump if can't follow suit but hold trump.
          3. Otherwise any card is legal.
        """
        if not original_suite:
            return list(player_hand)
        if self._has_suit(player_hand, original_suite):
            return [c for c in player_hand if c.getSuit() == original_suite]
        if mundup and self._has_suit(player_hand, mundup):
            return [c for c in player_hand if c.getSuit() == mundup]
        return list(player_hand)

    def _best_lead(self, hand, cards_remaining, mundup):
        """Choose best card when leading (no current highest on table)."""
        from collections import Counter

        # Lead with an Ace if we have one
        aces = [c for c in hand if c.getValue() == 14]
        if aces:
            # Among aces, prefer the one whose suit we hold most of
            suit_counts = Counter(c.getSuit() for c in hand)
            return max(aces, key=lambda c: suit_counts[c.getSuit()])

        # Otherwise lead the highest card of our most-held suit
        suit_counts = Counter(c.getSuit() for c in hand)
        dominant = max(suit_counts, key=suit_counts.get)
        return max((c for c in hand if c.getSuit() == dominant),
                   key=lambda c: c.getValue())

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