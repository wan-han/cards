import json
import csv
import os
from datetime import datetime, timezone
import random

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
    # No existing cards.json found in candidates — create a template file
    target_dir = os.path.normpath(os.path.join(BASE_DIR, "cardData"))
    os.makedirs(target_dir, exist_ok=True)
    CARDS_FILE = os.path.join(target_dir, "cards.json")

    template = [
        {
            "card_id": "pending",
            "holder": "pending",
            "role": "pending",
            "status": "pending",
            "allowed_doors": [],
            "payment": {
                "wallet_linked": False,
                "wallet_provider": None,
                "payment_tokens": [],
                "daily_offline_limit_gbp": 0,
            },
            "biometric": {
                "fingerprint_enrolled": False,
                "fingerprint_hash": None,
                "requires_card_pin": False,
            },
            "meta": {"issued_at": None, "issued_by": "pending", "notes": "pending"},
        }
    ]

    # write template if missing (don't clobber existing file if race)
    if not os.path.exists(CARDS_FILE):
        with open(CARDS_FILE, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2)
        print(f"Created template cards file at: {CARDS_FILE}")

print("Loading cards from:", CARDS_FILE)

EVENTS_FILE = "events.csv"
DOOR_ID = None


def load_cards():
    if CARDS_FILE is not None:
        """Load cards.json and return {card_id: card_dict}."""
        with open(CARDS_FILE, "r") as f:
            data = json.load(f)
        # expect a list like [ {...}, {...} ]
        cards_dict = {c["card_id"]: c for c in data}
        print(f"loaded {len(cards_dict)} cards")
        return cards_dict
    else:
        raise FileNotFoundError("CARDS_FILE is not set.")


# load once at startup
cards = load_cards()

# 2) simple policy
POLICY = {
    "door_1": ["admin", "staff"],
    "door_2": ["staff"],
    "door_3": ["admin", "user", "staff"],
    "lab_1": ["admin"],
    "lobby": ["admin", "staff", "guest", "user"],
}


def ensure_log():
    if not os.path.exists(EVENTS_FILE) or os.stat(EVENTS_FILE).st_size == 0:
        with open(EVENTS_FILE, "w", newline="") as f:
            out = csv.writer(f)
            out.writerow(
                [
                    "ts",
                    "door",
                    "card",
                    "holder",
                    "role",
                    "status",
                    "action",
                    "result",
                    "reason",
                ]
            )


def log_event(door_id, card, action, result, reason=""):
    ensure_log()
    if card is None:
        card = {}
    with open(EVENTS_FILE, "a", newline="") as f:
        out = csv.writer(f)
        out.writerow(
            [
                datetime.now(timezone.utc).isoformat(),
                DOOR_ID,
                door_id,
                card.get("card_id", "-"),
                card.get("holder", "-"),
                card.get("role", "-"),
                card.get("status", "-"),
                action,
                result,
                reason,
            ]
        )


def authorise(card_id, door_id):
    # 1) unknown card
    card = cards.get(card_id)
    if not card:
        log_event(door_id, {"card_id": card_id}, "access", "denied", "unknown card")
        return False, "Denied: unknown card."

    # 2) status check
    print(card.get("status"))
    if card.get("status") != "active":
        log_event(
            door_id, card, "access", "denied", f"Card status is {card.get('status')}"
        )
        return False, f"Denied: Card status is {card.get('status')}."

    # 3) door known?
    if door_id not in POLICY:
        # we can still allow if card explicitly allows it
        allowed_doors = card.get("allowed_doors")
        if not allowed_doors or door_id not in allowed_doors:
            log_event(
                door_id, card, "access", "denied", f"door '{door_id}' not recognized"
            )
            return False, f"Denied: door '{door_id}' not recognized."

    # 4) card-specific allowed_doors wins
    allowed_doors = card.get("allowed_doors")
    if allowed_doors is not None:
        if door_id not in allowed_doors:
            log_event(
                door_id,
                card,
                "access",
                "denied",
                f"door '{door_id}' not in card allowed doors",
            )
            return False, "Denied: door not in card allowed doors."

    # 5) role-based fallback
    role = card.get("role")
    permitted_roles = POLICY.get(door_id, [])
    if role not in permitted_roles:
        log_event(
            door_id,
            card,
            "access",
            "denied",
            f"role '{role}' not permitted for {door_id}",
        )
        return False, f"Denied: role '{role}' not permitted for {door_id}."

    # 6) success
    log_event(door_id, card, "access", "allowed", "ok")
    return True, "Access granted."


if __name__ == "__main__":
    help_text = (
        "Commands:\n"
        "  scan <card_id>   - simulate scanning a card\n"
        "  door <door_id>   - change current door\n"
        "  reload           - reload cards.json from disk\n"
        "  ?                - show this help message\n"
        "  exit             - quit\n"
    )

    while True:
        try:
            # chooses an initial door for this runtime
            DOOR_ID = random.choice(list(POLICY.keys()))
            print("Current random DOOR_ID:", DOOR_ID)

            print(help_text)
            cmd = input("Enter an action here> ").strip()
        except EOFError:
            print("EOF received, exiting")
            break

        if not cmd:
            continue

        parts = cmd.split()
        action = parts[0].lower()

        if action == "scan":
            if len(parts) < 2:
                print("Usage: scan <card_id>")
                continue
            card_id = parts[1]
            ok, msg = authorise(card_id, DOOR_ID)
            print("Result:", ok, "| Message:", msg)

        elif action == "door":
            if len(parts) < 2:
                print("Usage: door <door_id>")
                continue
            DOOR_ID = parts[1]
            print(f"Door set to: {DOOR_ID}")

        elif action == "reload":
            cards = load_cards()
            print(f"Reloaded {len(cards)} cards")

        elif action in ("exit", "quit"):
            print("Exiting")
            break

        elif action in ("help", "h", "?"):
            print(help_text)

        else:
            print("Unknown command. Type 'help' for commands.")
        print("Do you wish to continue? (y/n): ")
        cont = input("> ").strip().lower()
        if cont != "y":
            if cont != "n":
                print("Invalid input, exiting.")
                break
            print("Exiting.")
            break
