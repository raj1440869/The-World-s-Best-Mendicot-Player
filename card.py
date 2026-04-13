class Card:
    def __init__(self, suit, value):
        # 1. Normalize Suit (Handle plurals/caps)
        temp_suit = suit.capitalize()
        if not temp_suit.endswith('s'):
            self.suit = temp_suit + "s"
        else:
            self.suit = temp_suit

        # count is set externally by Deck; initialize to 0 so repr() never crashes
        self.count = 0

        # 2. Value Logic
        if isinstance(value, str):
            mapping = {"Jack": 11, "Queen": 12, "King": 13, "Ace": 14}
            formatted_value = value.capitalize()
            
            if formatted_value in mapping:
                self.value = mapping[formatted_value]
            elif value.isdigit():
                int_val = int(value)
                # Re-use the helper method to avoid duplicate code
                self.value = self._normalize_int_value(int_val)
            else:
                self.value = 2      
        
        elif isinstance(value, int):
            # FIX: Apply the same clamping logic to raw integers!
            self.value = self._normalize_int_value(value)

    # Helper function to keep logic clean and consistent
    def _normalize_int_value(self, val):
        if val <= 1:
            return 2
        elif val > 14:
            return 14  # This ensures 100 -> 14 (Ace)
        else:
            return val

    def getValue(self):
        return self.value

    def getSuit(self):
        return self.suit

    def getCount(self):
        return self.count

    def __repr__(self):
        name_map = {11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}
        val = name_map.get(self.value, str(self.value))
        return f"{val} of {self.suit}"