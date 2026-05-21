from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import BASE_DIR, get_connection, initialize_database
from .schemas import (
    Card,
    CardCreate,
    CardUpdate,
    Event,
    Reader,
    ReaderCreate,
    ReaderUpdate,
    ScanRequest,
    ScanResponse,
)

app = FastAPI(
    title="Cards API",
    description="Programmable NFC card access-control MVP.",
    version="0.1.0",
)

STATIC_DIR = BASE_DIR / "dashboard"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup():
    initialize_database()


@app.get("/")
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


def row_to_card(row, allowed_readers):
    return Card(
        card_id=row["card_id"],
        holder=row["holder"],
        role=row["role"],
        status=row["status"],
        wallet_linked=bool(row["wallet_linked"]),
        wallet_provider=row["wallet_provider"],
        daily_offline_limit_gbp=row["daily_offline_limit_gbp"],
        fingerprint_enrolled=bool(row["fingerprint_enrolled"]),
        requires_card_pin=bool(row["requires_card_pin"]),
        notes=row["notes"],
        allowed_readers=allowed_readers,
    )


def get_card_or_404(conn, card_id):
    card = conn.execute("SELECT * FROM cards WHERE card_id = ?", (card_id,)).fetchone()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


def get_reader_or_404(conn, reader_id):
    reader = conn.execute(
        "SELECT * FROM readers WHERE reader_id = ?", (reader_id,)
    ).fetchone()
    if reader is None:
        raise HTTPException(status_code=404, detail="Reader not found")
    return reader


def get_allowed_readers(conn, card_id):
    rows = conn.execute(
        "SELECT reader_id FROM card_permissions WHERE card_id = ? ORDER BY reader_id",
        (card_id,),
    ).fetchall()
    return [row["reader_id"] for row in rows]


def set_allowed_readers(conn, card_id, allowed_readers):
    if allowed_readers:
        placeholders = ", ".join("?" for _ in allowed_readers)
        rows = conn.execute(
            f"SELECT reader_id FROM readers WHERE reader_id IN ({placeholders})",
            allowed_readers,
        ).fetchall()
        known_readers = {row["reader_id"] for row in rows}
        missing_readers = sorted(set(allowed_readers) - known_readers)
        if missing_readers:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown readers: {', '.join(missing_readers)}",
            )

    conn.execute("DELETE FROM card_permissions WHERE card_id = ?", (card_id,))
    conn.executemany(
        """
        INSERT OR IGNORE INTO card_permissions (card_id, reader_id)
        VALUES (?, ?)
        """,
        [(card_id, reader_id) for reader_id in allowed_readers],
    )


@app.get("/cards", response_model=list[Card])
def list_cards():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM cards ORDER BY card_id").fetchall()
        return [row_to_card(row, get_allowed_readers(conn, row["card_id"])) for row in rows]


@app.post("/cards", response_model=Card, status_code=201)
def create_card(payload: CardCreate):
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM cards WHERE card_id = ?", (payload.card_id,)
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="Card already exists")

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
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.card_id,
                payload.holder,
                payload.role,
                payload.status,
                int(payload.wallet_linked),
                payload.wallet_provider,
                payload.daily_offline_limit_gbp,
                int(payload.fingerprint_enrolled),
                int(payload.requires_card_pin),
                payload.notes,
            ),
        )
        set_allowed_readers(conn, payload.card_id, payload.allowed_readers)
        card = get_card_or_404(conn, payload.card_id)
        return row_to_card(card, get_allowed_readers(conn, payload.card_id))


@app.patch("/cards/{card_id}", response_model=Card)
def update_card(card_id: str, payload: CardUpdate):
    fields = payload.dict(exclude_unset=True)
    allowed_readers = fields.pop("allowed_readers", None)

    with get_connection() as conn:
        get_card_or_404(conn, card_id)

        if fields:
            assignments = ", ".join([f"{field} = ?" for field in fields])
            values = [
                int(value) if isinstance(value, bool) else value
                for value in fields.values()
            ]
            conn.execute(
                f"UPDATE cards SET {assignments} WHERE card_id = ?",
                [*values, card_id],
            )

        if allowed_readers is not None:
            set_allowed_readers(conn, card_id, allowed_readers)

        card = get_card_or_404(conn, card_id)
        return row_to_card(card, get_allowed_readers(conn, card_id))


@app.get("/readers", response_model=list[Reader])
def list_readers():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM readers ORDER BY reader_id").fetchall()
        return [Reader(**dict(row)) for row in rows]


@app.post("/readers", response_model=Reader, status_code=201)
def create_reader(payload: ReaderCreate):
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM readers WHERE reader_id = ?", (payload.reader_id,)
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="Reader already exists")

        conn.execute(
            """
            INSERT INTO readers (reader_id, name, location, action_type, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.reader_id,
                payload.name,
                payload.location,
                payload.action_type,
                payload.status,
            ),
        )
        reader = get_reader_or_404(conn, payload.reader_id)
        return Reader(**dict(reader))


@app.patch("/readers/{reader_id}", response_model=Reader)
def update_reader(reader_id: str, payload: ReaderUpdate):
    fields = payload.dict(exclude_unset=True)

    with get_connection() as conn:
        get_reader_or_404(conn, reader_id)

        if fields:
            assignments = ", ".join([f"{field} = ?" for field in fields])
            conn.execute(
                f"UPDATE readers SET {assignments} WHERE reader_id = ?",
                [*fields.values(), reader_id],
            )

        reader = get_reader_or_404(conn, reader_id)
        return Reader(**dict(reader))


@app.post("/scan", response_model=ScanResponse)
def scan(payload: ScanRequest):
    with get_connection() as conn:
        card = conn.execute(
            "SELECT * FROM cards WHERE card_id = ?", (payload.card_id,)
        ).fetchone()
        reader = conn.execute(
            "SELECT * FROM readers WHERE reader_id = ?", (payload.reader_id,)
        ).fetchone()

        allowed = False
        action = "deny"
        reason = "unknown card"

        if card is None:
            holder = None
            role = None
        else:
            holder = card["holder"]
            role = card["role"]
            if card["status"] != "active":
                reason = f"card status is {card['status']}"
            elif reader is None:
                reason = "unknown reader"
            elif reader["status"] != "active":
                reason = f"reader status is {reader['status']}"
            else:
                permission = conn.execute(
                    """
                    SELECT 1 FROM card_permissions
                    WHERE card_id = ? AND reader_id = ?
                    """,
                    (payload.card_id, payload.reader_id),
                ).fetchone()
                if permission is None:
                    reason = "card is not permitted for this reader"
                else:
                    allowed = True
                    action = reader["action_type"]
                    reason = "ok"

        result = "allowed" if allowed else "denied"
        conn.execute(
            """
            INSERT INTO events (
                ts,
                card_id,
                reader_id,
                holder,
                role,
                action,
                result,
                reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                payload.card_id,
                payload.reader_id,
                holder,
                role,
                action,
                result,
                reason,
            ),
        )

        return ScanResponse(
            allowed=allowed,
            action=action,
            result=result,
            reason=reason,
            card_id=payload.card_id,
            reader_id=payload.reader_id,
        )


@app.get("/events", response_model=list[Event])
def list_events(limit: int = 50):
    limit = min(max(limit, 1), 200)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [Event(**dict(row)) for row in rows]
