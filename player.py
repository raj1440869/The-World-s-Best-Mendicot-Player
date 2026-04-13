class Player:
    def __init__(self, team, player_num, name=""):
        self.team = team
        self.player_num = player_num
        self.name = name if name else f"Player {player_num}"
        self.hand = []
        self.teammates = []
    
    def add_card(self, card):
        """Add a card to the player's hand"""
        self.hand.append(card)
    
    def add_teammate(self, teammate):
        """Add a teammate to this player's teammate list"""
        self.teammates.append(teammate)
    
    def __repr__(self):
        """Display player info including all cards in hand"""
        # Name map for face cards
        name_map = {11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}
        
        # Format the hand
        card_strings = []
        for card in self.hand:
            value = card.getValue()
            suit = card.getSuit()
            
            # Convert numeric values to card names
            if value in name_map:
                display_value = name_map[value]
            else:
                display_value = str(value)
            
            card_strings.append(f"{display_value} of {suit}")
        
        # Format teammate info
        teammate_names = [t.name for t in self.teammates]
        teammates_str = ", ".join(teammate_names) if teammate_names else "None"
        
        # Build the representation string
        result = f"\n{'='*60}\n"
        result += f"TEAM {self.team} - {self.name.upper()}\n"
        result += f"{'='*60}\n"
        result += f"Teammates: {teammates_str}\n"
        result += f"Cards in Hand ({len(self.hand)}):\n"
        result += "-" * 60 + "\n"
        
        if card_strings:
            for i, card_str in enumerate(card_strings, 1):
                result += f"  {i:2}. {card_str}\n"
        else:
            result += "  (No cards)\n"
        
        result += "=" * 60
        
        return result