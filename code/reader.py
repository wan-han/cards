import json
import csv
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(__file__)

CANDIDATES = [
    "cards.json",
    os.path.join("cards", "code", "cardData", "cards.json"),
    os.path.join("cards", "code", "cards.json"),
    os.path.join("cardData", "cards.json"),
    os.path.join("..", "cardData", "cards.json"),
    os.path.join("..", "cards.json"),
]

CARDS_FILE = None
for rel in CANDIDATES:
    candidate = os.path.normpath(os.path.join(BASE_DIR, rel))
    if os.path.exists(candidate):
        CARDS_FILE = candidate
        break
else:
    raise FileNotFoundError(f"cards.json not found; tried {CANDIDATES} from {BASE_DIR}")

print("Loading cards from:", CARDS_FILE)

EVENTS_FILE = "events.csv"
DOOR_ID = "door_1"

def load_cards():
    """Load cards.json and return {card_id: card_dict}."""
    with open(CARDS_FILE, "r") as f:
        data = json.load(f)
    # expect a list like [ {...}, {...} ]
    cards_dict = {c["card_id"]: c for c in data}
    print(f"loaded {len(cards_dict)} cards")
    return cards_dict

# load once at startup
cards = load_cards()

# 2) simple policy
POLICY = {
    "door_1": ["admin", "staff"],
    "lab_2": ["admin"],
    "lobby": ["admin", "staff", "guest"],
}

def ensure_log():
    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "w", newline="") as f:
            out = csv.writer(f)
            out.writerow(["ts","door","card","holder","role","status","action","result","reason"])

def log_event(door_id, card, action, result, reason=""):
    ensure_log()
    with open(EVENTS_FILE, "a", newline="") as f:
        out = csv.writer(f)
        out.writerow([
            datetime.now(timezone.utc).isoformat(), DOOR_ID,
            door_id,
            card.get("card_id","-"),
            card.get("holder","-"),
            card.get("role","-"),
            card.get("status","-"),
            action, result, reason
        ])

def authorize(card_id, door_id):
    # 1) unknown card
    card = cards.get(card_id)
    if not card:
        return False, "Denied: unknown card."

    # 2) status check
    print(card.get("status"))
    if card.get("status") != "active":
        return False, f"Denied: Card status is {card.get('status')}."

    # 3) door known?


    # 4) card-specific allowed_doors wins


    # 5) role-based fallback


    # 6) success
    log_event(door_id, card, "access", "allowed", "ok")
    return True, "Access granted."



if __name__ == "__main__":
    while True:
        print("Enter card ID to test: ")
        test_id = input("> ").strip()
        ok, msg = authorize(test_id, DOOR_ID)
        print("Result:", ok, "| Message:", msg)