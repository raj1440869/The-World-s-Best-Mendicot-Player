# The World's Best Mendicot Player

An AI-powered advisor for the **Mendicot** trick-taking card game.

## What it does

You play cards physically at the table. This tool:
- Tracks all four players' hands and the running game state
- Calculates the **probability of losing** for every card you could play
- Flags illegal moves (playing off-suit when you must follow)
- Optionally detects cards from a webcam via a YOLOv5 model

## Game rules (quick summary)

| Item | Detail |
|---|---|
| Players | 4 (2 teams of 2, seated alternately) |
| Deck | Standard 52-card deck |
| Cards each | 13 |
| Goal | Capture the most **Aces** |
| Trump (mundup) | Set by the first player who breaks suit |

## Project structure

| File | Purpose |
|---|---|
| `card.py` | Card data class (suit, value, normalization) |
| `deck.py` | 52-card deck with dealing and removal |
| `player.py` | Player model (hand, team, teammates) |
| `calculations.py` | Loss-probability engine (core AI) |
| `game.py` | Game state manager (tricks, mundup, scoring) |
| `main.py` | Interactive CLI advisor — **start here** |
| `detectcard.py` | Optional YOLOv5 camera detection |

## Quick start

```bash
# Manual mode (no camera required)
python main.py

# Random deal for testing
python main.py --random-deal

# Camera mode (requires best.pt model weights)
python main.py --camera
```

During play, type at any prompt:
- `advice` — see AI loss-probability for every card in your hand
- `hand` — redisplay your hand
- `state` — show current trick, mundup, and Ace counts
- `1`–`13` — play card by number
- `K h` / `Ace Clubs` — play card by name

## Camera detection setup (optional)

1. Clone [PD-Mera/Playing-Cards-Detection](https://github.com/PD-Mera/Playing-Cards-Detection)
2. Download `best.pt` and place it in this directory
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py --camera`

The core advisor (`main.py`) works without any of the above.

## How the AI works

`calculations.py` implements Mendicot-aware probability:

- **Setting mundup** — you break suit; your card's suit becomes trump
- **Playing mundup** — count how many higher trump cards remain
- **Following suit** — count how many higher same-suit cards remain
- **Illegal move** — flagged when you hold the led suit but try to play another

Each card in your hand gets a **% chance of losing** so you can pick the safest play.
