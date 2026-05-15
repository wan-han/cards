import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "cards.db"
SEED_CARDS_PATH = BASE_DIR / "code" / "cardData" / "cards.json"

DEFAULT_READERS = [
    {
        "reader_id": "door_1",
        "name": "Front Door",
        "location": "House",
        "action_type": "unlock",
        "status": "active",
    },
    {
        "reader_id": "door_2",
        "name": "Studio Door",
        "location": "House",
        "action_type": "unlock",
        "status": "active",
    },
    {
        "reader_id": "lobby",
        "name": "Lobby Reader",
        "location": "Event Space",
        "action_type": "check_in",
        "status": "active",
    },
    {
        "reader_id": "door_3",
        "name": "Garden Room",
        "location": "House",
        "action_type": "unlock",
        "status": "active",
    },
    {
        "reader_id": "lab_1",
        "name": "Private Room",
        "location": "Restricted Area",
        "action_type": "unlock",
        "status": "active",
    },
]


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cards (
                card_id TEXT PRIMARY KEY,
                holder TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                wallet_linked INTEGER NOT NULL DEFAULT 0,
                wallet_provider TEXT,
                daily_offline_limit_gbp INTEGER NOT NULL DEFAULT 0,
                fingerprint_enrolled INTEGER NOT NULL DEFAULT 0,
                requires_card_pin INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                issued_at TEXT,
                issued_by TEXT
            );

            CREATE TABLE IF NOT EXISTS readers (
                reader_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT,
                action_type TEXT NOT NULL DEFAULT 'unlock',
                status TEXT NOT NULL DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS card_permissions (
                card_id TEXT NOT NULL,
                reader_id TEXT NOT NULL,
                PRIMARY KEY (card_id, reader_id),
                FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE,
                FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                card_id TEXT NOT NULL,
                reader_id TEXT NOT NULL,
                holder TEXT,
                role TEXT,
                action TEXT NOT NULL,
                result TEXT NOT NULL,
                reason TEXT NOT NULL
            );
            """
        )
        seed_database(conn)


def seed_database(conn):
    card_count = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    reader_count = conn.execute("SELECT COUNT(*) FROM readers").fetchone()[0]

    if reader_count == 0:
        conn.executemany(
            """
            INSERT INTO readers (reader_id, name, location, action_type, status)
            VALUES (:reader_id, :name, :location, :action_type, :status)
            """,
            DEFAULT_READERS,
        )

    if card_count > 0 or not SEED_CARDS_PATH.exists():
        return

    with SEED_CARDS_PATH.open("r", encoding="utf-8") as f:
        cards = json.load(f)

    for card in cards:
        payment = card.get("payment", {})
        biometric = card.get("biometric", {})
        meta = card.get("meta", {})
        conn.execute(
            """
            INSERT INTO cards (
                card_id,
                holder,
                role,
                status,
                wallet_linked,
                wallet_provider,
                daily_offline_limit_gbp,
                fingerprint_enrolled,
                requires_card_pin,
                notes,
                issued_at,
                issued_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card["card_id"],
                card["holder"],
                card["role"],
                card["status"],
                int(payment.get("wallet_linked", False)),
                payment.get("wallet_provider"),
                payment.get("daily_offline_limit_gbp", 0),
                int(biometric.get("fingerprint_enrolled", False)),
                int(biometric.get("requires_card_pin", False)),
                meta.get("notes"),
                meta.get("issued_at"),
                meta.get("issued_by"),
            ),
        )

        for reader_id in card.get("allowed_doors", []):
            conn.execute(
                """
                INSERT OR IGNORE INTO card_permissions (card_id, reader_id)
                VALUES (?, ?)
                """,
                (card["card_id"], reader_id),
            )
