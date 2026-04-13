#!/usr/bin/env python3
"""
The World's Best Mendicot Player – AI Advisor
=============================================
A CLI advisor for the Mendicot trick-taking card game.

You play cards physically; this program:
  • Tracks hands, tricks, and game state
  • Calculates the probability of losing for every card in your hand
  • Tells you the safest card to play

Usage:
    python main.py                # Manual hand-entry mode (default)
    python main.py --camera       # Camera detection mode (requires best.pt)
    python main.py --random-deal  # Random deal for quick testing
"""

import sys
import argparse
from game import Game
from card import Card

# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

RANK_MAP = {
    "a": "Ace", "ace": "Ace",
    "j": "Jack", "jack": "Jack",
    "q": "Queen", "queen": "Queen",
    "k": "King", "king": "King",
}

SUIT_MAP = {
    "c": "Clubs",    "club": "Clubs",    "clubs": "Clubs",
    "d": "Diamonds", "diamond": "Diamonds", "diamonds": "Diamonds",
    "h": "Hearts",   "heart": "Hearts",  "hearts": "Hearts",
    "s": "Spades",   "spade": "Spades",  "spades": "Spades",
}

VALID_SUITS = {"Clubs", "Diamonds", "Hearts", "Spades"}


def parse_card_input(text):
    """
    Parse a card string like "Ace Hearts", "K s", "10 d", "2 clubs".
    Returns (suit: str, value: str|int) or raises ValueError.
    """
    parts = text.strip().lower().split()
    if len(parts) < 2:
        raise ValueError("Need rank AND suit, e.g. 'Ace Hearts' or 'K s'")

    rank_str, suit_str = parts[0], parts[1]

    # Resolve rank
    if rank_str in RANK_MAP:
        value = RANK_MAP[rank_str]
    elif rank_str.isdigit():
        value = int(rank_str)
    else:
        raise ValueError(f"Unknown rank: '{rank_str}'")

    # Resolve suit
    if suit_str in SUIT_MAP:
        suit = SUIT_MAP[suit_str]
    else:
        raise ValueError(f"Unknown suit: '{suit_str}'")

    return suit, value


def prompt_card(prompt_text):
    """Loop until the user enters a valid card. Returns (suit, value)."""
    while True:
        try:
            raw = input(prompt_text).strip()
            if not raw:
                continue
            return parse_card_input(raw)
        except ValueError as e:
            print(f"    Invalid: {e}. Try: 'Ace Hearts', 'K s', '10 d', '2 clubs'")


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

FACE_NAMES = {11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}


def card_display(card):
    val = FACE_NAMES.get(card.getValue(), str(card.getValue()))
    return f"{val} of {card.getSuit()}"


def show_hand(player):
    print(f"\n  {player.name}'s hand:")
    print("  " + "-" * 38)
    for i, card in enumerate(player.hand, 1):
        print(f"    [{i:2}] {card_display(card)}")
    print("  " + "-" * 38)


# ---------------------------------------------------------------------------
# Setup phase
# ---------------------------------------------------------------------------

def setup_players(game):
    print("\n" + "=" * 60)
    print("  MENDICOT SETUP")
    print("=" * 60)
    print("  Seating: P1, P2, P3, P4  (sit in this order around the table)")
    print("  Team 1 = P1 & P3   |   Team 2 = P2 & P4")
    print()

    names = []
    for i in range(4):
        team = 1 if i % 2 == 0 else 2
        default = f"Player {i + 1}"
        raw = input(f"  Player {i + 1} (Team {team}) name [{default}]: ").strip()
        names.append(raw if raw else default)

    game.setup(names)
    print(f"\n  Team 1: {names[0]} & {names[2]}")
    print(f"  Team 2: {names[1]} & {names[3]}")


def deal_manually(game):
    print("\n" + "=" * 60)
    print("  DEAL CARDS  (enter each player's 13 cards)")
    print("=" * 60)
    print("  Format: <rank> <suit>")
    print("  Ranks : 2-10, J/Jack, Q/Queen, K/King, A/Ace")
    print("  Suits : c/Clubs  d/Diamonds  h/Hearts  s/Spades")
    print()

    for i, player in enumerate(game.players):
        print(f"\n  --- {player.name} (Team {player.team}) ---")
        for n in range(1, 14):
            suit, value = prompt_card(f"    Card {n:2}/13: ")
            card = game.add_card_to_hand(i, suit, value)
            print(f"      Added: {card}")


def deal_randomly(game):
    game.deal_from_deck()
    print("\n  Cards dealt randomly (testing mode).")
    for p in game.players:
        show_hand(p)


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def run_game(game, camera_mode=False):
    detector = None
    if camera_mode:
        try:
            from detectcard import CNNCardDetector
            detector = CNNCardDetector()
            detector.clear_played_cards()   # fresh start for this game
            print("\n  Camera detection enabled.")
            print("  The camera will scan for played cards automatically each turn.")
            print("  Point camera at played cards / discard area.")
        except Exception as exc:
            print(f"\n  Camera unavailable ({exc}). Using manual input.")

    print("\n" + "=" * 60)
    print("  GAME START")
    print("=" * 60)
    print("  Commands during your turn:")
    print("    advice  – full loss-probability breakdown for each card")
    print("    hand    – show your current hand")
    print("    state   – show full game state")
    print("    scan    – manually trigger a camera scan for played cards")
    print("    <N>     – play card number N from your hand")
    print("    <card>  – play by name, e.g. 'K h' or 'Ace Clubs'")
    print()
    print("  The BEST PLAY is shown automatically at the start of each turn.")
    print()

    for trick_num in range(1, 14):
        print(f"\n{'=' * 60}")
        print(f"  TRICK {trick_num}")
        print(f"{'=' * 60}")
        print(" ", game.state_summary().replace("\n", "\n  "))

        for _ in range(4):
            pidx = game.current_player
            player = game.players[pidx]

            print(f"\n  {player.name}'s turn  (Team {player.team})")
            show_hand(player)

            # Auto-scan camera and show the best play at the start of every turn
            if camera_mode and detector:
                new_cards = detector.scan_and_accumulate()
                if new_cards:
                    print(f"  [camera] Detected {len(new_cards)} newly played card(s).")

            best = game.get_best_move(pidx, detector if camera_mode else None)
            if best:
                print(f"\n  >>> BEST PLAY: {best} <<<")

            card_played = None
            while card_played is None:
                raw = input("  > ").strip()
                if not raw:
                    continue
                cmd = raw.lower()

                if cmd == "advice":
                    advice = game.get_advice(pidx, detector if camera_mode else None)
                    print("\n  AI ADVICE (loss probability per card):")
                    for line in advice.splitlines():
                        print(f"    {line}")
                    print(f"\n  >>> BEST PLAY: {best} <<<")
                    continue

                if cmd == "hand":
                    show_hand(player)
                    continue

                if cmd == "state":
                    print("\n ", game.state_summary().replace("\n", "\n  "))
                    continue

                if cmd == "scan" and camera_mode and detector:
                    found = detector.scan_and_accumulate()
                    total = len(detector.played_cards_set)
                    print(f"  [camera] Scan complete. {len(found)} new card(s). "
                          f"Total seen: {total}.")
                    # Recompute best move with updated knowledge
                    best = game.get_best_move(pidx, detector)
                    print(f"  >>> BEST PLAY: {best} <<<")
                    continue

                if cmd == "camera" and detector:
                    obj = detector.get_current_card()
                    if obj:
                        print(f"  Camera: {obj}")
                        raw = f"{obj.getValue()} {obj.getSuit()}"
                    else:
                        print("  No card detected yet. Enter manually.")
                        continue

                # Try numeric index
                if raw.isdigit():
                    idx = int(raw) - 1
                    if 0 <= idx < len(player.hand):
                        card_played, trick_done, winner_idx = game.play_card(pidx, idx)
                    else:
                        print(f"  Enter 1–{len(player.hand)}")
                        continue
                else:
                    # Try card name
                    try:
                        suit, value = parse_card_input(raw)
                        target = Card(suit, value)
                    except ValueError as e:
                        print(f"  {e}")
                        continue

                    # Find card in hand
                    found_idx = None
                    for j, c in enumerate(player.hand):
                        if c.getSuit() == target.getSuit() and c.getValue() == target.getValue():
                            found_idx = j
                            break

                    if found_idx is None:
                        print(f"  '{target}' not in your hand.")
                        continue

                    card_played, trick_done, winner_idx = game.play_card(pidx, found_idx)

                print(f"  Played: {card_played}")

                if trick_done:
                    winner_name = game.players[winner_idx].name
                    winner_team = game.players[winner_idx].team
                    print(f"\n  {winner_name} (Team {winner_team}) wins trick {trick_num}!")
                    print(f"  Aces so far — Team 1: {game.aces_won[1]}, Team 2: {game.aces_won[2]}")
                    break   # inner while

            if trick_done:
                break   # inner for-range(4)

    # ------------------------------------------------------------------
    # Game over
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  GAME OVER")
    print("=" * 60)
    print(f"  Tricks — Team 1: {game.tricks_won[1]}, Team 2: {game.tricks_won[2]}")
    print(f"  Aces   — Team 1: {game.aces_won[1]},  Team 2: {game.aces_won[2]}")

    winner = game.get_winner()
    if winner:
        names = " & ".join(p.name for p in game.players if p.team == winner)
        print(f"\n  WINNER: Team {winner} ({names})!")
    else:
        print("\n  RESULT: TIE — both teams captured 2 Aces.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="The World's Best Mendicot Player – AI Advisor"
    )
    parser.add_argument(
        "--camera", action="store_true",
        help="Enable camera card detection (requires best.pt and torch/cv2)"
    )
    parser.add_argument(
        "--random-deal", action="store_true",
        help="Deal cards randomly (for testing without physical cards)"
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  THE WORLD'S BEST MENDICOT PLAYER")
    print("  AI-Powered Card Game Advisor")
    print("=" * 60)

    game = Game()
    setup_players(game)

    if args.random_deal:
        deal_randomly(game)
    else:
        deal_manually(game)

    # Show all hands before play begins
    print("\n" + "=" * 60)
    print("  ALL HANDS")
    print("=" * 60)
    for player in game.players:
        print(player)

    # Who leads first trick?
    while True:
        raw = input("\n  Which player leads first? (1–4): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= 4:
            game.current_player = int(raw) - 1
            game.trick_leader = game.current_player
            break
        print("  Enter 1, 2, 3, or 4")

    run_game(game, camera_mode=args.camera)


if __name__ == "__main__":
    main()
