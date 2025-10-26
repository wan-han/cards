# reader.py (start)
import json, csv, os
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)

CANDIDATES = [
    "cards.json",                           # same folder
    os.path.join("cardData", "cards.json"), # ./cardData/cards.json
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
    raise FileNotFoundError(
        f"cards.json not found; tried {CANDIDATES} from {BASE_DIR}"
    )

print("Loading cards from:", CARDS_FILE)  # debug; remove later

# CARDS_FILE = "cards.json"
EVENTS_FILE = "events.csv"
DOOR_ID = "door_1"

# 1) load cards into dict
with open(CARDS_FILE) as f:
    cards = {c["card_id"]: c for c in json.load(f)}

# 2) simple policy
POLICY = {
    "door_1": ["admin","staff"],
    "lab_2": ["admin"],
    "lobby": ["admin","staff","guest"]
}

def ensure_log():
    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "w", newline="") as f:
            out = csv.writer(f)
            out.writerow(["ts","door","card","holder","role","status","action","result","reason"])

def log_event(card, action, result, reason=""):
    ensure_log()
    with open(EVENTS_FILE, "a", newline="") as f:
        out = csv.writer(f)
        out.writerow([
            datetime.utcnow().isoformat(), DOOR_ID,
            card.get("card_id","-"),
            card.get("holder","-"),
            card.get("role","-"),
            card.get("status","-"),
            action, result, reason
        ])

# 3) implement authorize() and pay_simulation() below...
def authorize(card_id, door_id):
    if card_id not in cards:
        return False, "Denied, Unknown Card. "
    
    card = cards[card_id]

    print(card["status"])
    return True, "Access Granted, Card Recognised. "


if __name__ == "__main__":
    # manually test the authorize function
    test_id = input("Enter card ID to test: ").strip()
    ok, msg = authorize(test_id, DOOR_ID)
    print("Result:", ok, "| Message:", msg)