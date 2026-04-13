from card import Card
from deck import Deck
from player import Player
from calculations import Calculations


class Game:
    """
    Manages the state of a Mendicot game.

    Mendicot: 4-player trick-taking game, 2 teams of 2.
    13 cards each, dealt from a single 52-card deck.
    The team that captures the most Aces wins.

    Seating order: P1, P2, P3, P4
    Teams:  Team 1 = P1 & P3  |  Team 2 = P2 & P4
    """

    def __init__(self):
        self.calculations = Calculations()
        self.players = []           # List[Player], indices 0-3
        self.mundup = None          # Trump suit (str), set when first player breaks suit
        self.original_suite = None  # Suit led this trick (str)
        self.highest_card = None    # Current winning Card on the table
        self.highest_player = None  # Index of player holding the current best card
        self.current_trick = []     # [(player_index, Card), ...]
        self.played_cards = []      # All Card objects played so far (any trick)
        self.aces_won = {1: 0, 2: 0}
        self.tricks_won = {1: 0, 2: 0}
        self.current_player = 0    # Index of player whose turn it is
        self.trick_leader = 0      # Who leads the current trick

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(self, player_names):
        """
        Initialise players and register teammates.
        player_names: list of 4 strings.
        """
        if len(player_names) != 4:
            raise ValueError("Mendicot requires exactly 4 players.")

        self.players = []
        for i, name in enumerate(player_names):
            team = 1 if i % 2 == 0 else 2
            self.players.append(Player(team=team, player_num=i + 1, name=name))

        # Register teammates (P0<->P2, P1<->P3)
        self.players[0].add_teammate(self.players[2])
        self.players[2].add_teammate(self.players[0])
        self.players[1].add_teammate(self.players[3])
        self.players[3].add_teammate(self.players[1])

    def deal_from_deck(self):
        """Deal 13 random cards to each player (useful for testing)."""
        deck = Deck()
        for _ in range(13):
            for player in self.players:
                card = deck.dealRandomCard()
                if card:
                    player.add_card(card)

    def add_card_to_hand(self, player_index, suit, value):
        """Manually add one card to a player's hand. Returns the Card."""
        card = Card(suit, value)
        self.players[player_index].add_card(card)
        return card

    # ------------------------------------------------------------------
    # AI advice
    # ------------------------------------------------------------------

    def get_advice(self, player_index, detector=None):
        """
        Return a string with the loss-probability for each card in hand.
        Pass a CNNCardDetector to include camera-detected played cards.
        If the player is leading the trick, return a simple overview.
        """
        player = self.players[player_index]
        remaining = self._unknown_cards(player_index, detector)

        if not self.original_suite:
            lines = [
                "You lead this trick. Any card is valid.",
                f"Unknown cards still out: {len(remaining)}",
            ]
            return "\n".join(lines)

        return self.calculations.calculate_loss(
            original_suite=self.original_suite,
            mundup=self.mundup,
            highest_card=self.highest_card,
            player_hand=player.hand,
            cards_remaining=remaining,
        )

    def get_best_move(self, player_index, detector=None):
        """
        Return the single Card that is the mathematically best play.
        Pass a CNNCardDetector to include camera-detected played cards,
        giving the AI perfect knowledge of eliminated cards.
        """
        player = self.players[player_index]
        remaining = self._unknown_cards(player_index, detector)

        teammate_winning = False
        if self.highest_player is not None:
            my_team = self.players[player_index].team
            winner_team = self.players[self.highest_player].team
            teammate_winning = (winner_team == my_team)

        return self.calculations.best_move(
            original_suite=self.original_suite,
            mundup=self.mundup,
            highest_card=self.highest_card,
            player_hand=player.hand,
            cards_remaining=remaining,
            teammate_winning=teammate_winning,
        )

    def _unknown_cards(self, for_player_index, detector=None):
        """
        Cards not in the player's own hand and not yet played.
        If a CNNCardDetector is supplied its cumulative played_cards_set
        is also subtracted, using camera vision to refine the unknown set.
        """
        all_cards = {
            (suit, val)
            for suit in ["Clubs", "Diamonds", "Hearts", "Spades"]
            for val in range(2, 15)
        }

        # Remove own hand
        for card in self.players[for_player_index].hand:
            all_cards.discard((card.getSuit(), card.getValue()))

        # Remove manually tracked played cards
        for card in self.played_cards:
            all_cards.discard((card.getSuit(), card.getValue()))

        # Remove camera-detected played cards (may overlap with above, safe)
        if detector is not None:
            for card in detector.get_all_played_cards():
                all_cards.discard((card.getSuit(), card.getValue()))

        return [Card(s, v) for s, v in all_cards]

    # ------------------------------------------------------------------
    # Card play
    # ------------------------------------------------------------------

    def play_card(self, player_index, card_index):
        """
        Remove card at card_index from the player's hand and process it.

        Returns:
            (card_played, trick_complete, winner_index)
            trick_complete is True when all 4 players have played.
            winner_index is the player index who won the trick (or None).
        """
        player = self.players[player_index]
        card = player.hand.pop(card_index)

        if not self.current_trick:
            # First card of the trick sets the original suite
            self.original_suite = card.getSuit()
            self.highest_card = card
            self.highest_player = player_index
        else:
            # Check for mundup being set (first off-suit play when no trump yet)
            if self.mundup is None and card.getSuit() != self.original_suite:
                self.mundup = card.getSuit()

            # Update leading card if this one beats it
            if self._beats(card, self.highest_card):
                self.highest_card = card
                self.highest_player = player_index

        self.current_trick.append((player_index, card))
        self.played_cards.append(card)

        if len(self.current_trick) == 4:
            # Trick complete
            winner = self.highest_player
            team = self.players[winner].team
            self.tricks_won[team] += 1

            for _, c in self.current_trick:
                if c.getValue() == 14:   # Ace
                    self.aces_won[team] += 1

            # Reset trick state
            self.current_trick = []
            self.original_suite = None
            self.highest_card = None
            self.highest_player = None
            self.trick_leader = winner
            self.current_player = winner

            return card, True, winner
        else:
            self.current_player = (player_index + 1) % 4
            return card, False, None

    def _beats(self, challenger, current_best):
        """Return True if challenger beats the current best card."""
        c_suit = challenger.getSuit()
        b_suit = current_best.getSuit()
        c_val = challenger.getValue()
        b_val = current_best.getValue()

        if self.mundup:
            if c_suit == self.mundup and b_suit != self.mundup:
                return True
            if c_suit == self.mundup and b_suit == self.mundup:
                return c_val > b_val
            if c_suit != self.mundup and b_suit == self.mundup:
                return False

        # No mundup in play (or neither card is mundup): must follow suit and be higher
        return c_suit == b_suit and c_val > b_val

    # ------------------------------------------------------------------
    # Scoring / summary
    # ------------------------------------------------------------------

    def get_winner(self):
        """Return winning team number (1 or 2), or None on a 2-2 Ace tie."""
        if self.aces_won[1] > self.aces_won[2]:
            return 1
        if self.aces_won[2] > self.aces_won[1]:
            return 2
        return None   # 2-2 split

    def state_summary(self):
        """One-line summary of the current game state."""
        trick_num = self.tricks_won[1] + self.tricks_won[2] + len(self.current_trick) // 4 + 1
        trick_num = min(trick_num, 13)
        current_cards = ", ".join(
            f"{self.players[pi].name}: {c}" for pi, c in self.current_trick
        )
        return (
            f"Trick {trick_num} | Mundup: {self.mundup or 'none'} | "
            f"Lead suit: {self.original_suite or 'none'} | "
            f"Best card: {self.highest_card or 'none'}\n"
            f"Table: {current_cards or '(empty)'}\n"
            f"Aces — Team 1: {self.aces_won[1]}, Team 2: {self.aces_won[2]}"
        )
