# Cards

Cards is an early-stage programmable NFC card platform for custom access control, event interactions, and future wallet-style integrations.

The aim is to let an owner issue custom physical cards and decide how different readers respond when each card is tapped. A card could unlock a door, validate a guest, trigger an activity, deduct internal credits, or be denied based on rules controlled through a dashboard.

The long-term vision is a polished hardware and software product for homes, private venues, events, offices, rentals, and small businesses.

## Product Vision

Most access systems are rigid: one card, one purpose, one set of permissions.

Cards is designed around programmable behaviour:

- different readers can perform different actions
- different cards can trigger different outcomes
- owners can manage cards, readers, permissions, and logs
- cards can be activated, revoked, or limited by role, location, or use case
- future modules can support credits, internal wallets, and regulated payment integrations

Example:

```text
Card A tapped on Front Door Reader
-> validate card status
-> check door permission
-> unlock door
-> log access event

Card B tapped on Event Reader
-> validate guest
-> mark attendance
-> trigger custom activity
-> log event
```

## Current MVP

This repository now contains a small FastAPI backend, SQLite database, and owner dashboard for the core authorisation flow.

It supports:

- card data stored in SQLite
- seeded sample data from JSON
- reader records and reader-specific actions
- active and inactive card status checks
- card-specific reader permissions
- unknown card and unknown reader handling
- event logging to the database
- owner dashboard for scans, cards, readers, and audit events
- legacy command-line simulation in `code/reader.py`

This is not yet connected to physical NFC hardware. That is the next major product step.

## Architecture

```text
NFC Card
  -> Reader Device
  -> Backend API
  -> Rules Engine
  -> Database
  -> Action
  -> Dashboard + Audit Logs
```

Near-term architecture:

- NFC card/tag stores a unique card identifier
- reader device sends card ID and reader ID to the backend
- backend checks card status, permissions, and rules
- backend returns an action such as allow, deny, unlock, deduct credit, or trigger event
- dashboard lets the owner manage cards, readers, rules, and logs

## Repository Structure

```text
.
+-- app/
|   +-- main.py                # FastAPI app and API routes
|   +-- database.py            # SQLite schema and seed logic
|   +-- schemas.py             # Request/response models
+-- dashboard/
|   +-- index.html             # Owner dashboard
|   +-- styles.css
|   +-- app.js
+-- code/
|   +-- reader.py              # Legacy CLI prototype
|   +-- events.example.csv
|   +-- cardData/
|       +-- cards.json         # Seed card data
|       +-- DataInfo.txt       # Card data schema notes
+-- docs/
|   +-- ROADMAP.md             # Product and engineering roadmap
+-- requirements.txt
+-- .gitignore
+-- README.md
```

## Run Locally

Requires Python 3.10+.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

API docs are available at `http://127.0.0.1:8000/docs`.

The old CLI prototype can still be run with `python code/reader.py`.

## Mock Reader Client

The mock reader client behaves like a future NFC reader device: it knows its own `reader_id`, accepts card IDs from the terminal, and sends scan requests to the backend.

```bash
python -m reader_client.mock_reader --reader-id door_1 --api-url http://127.0.0.1:8000
```

Example:

```text
card> A001
ALLOWED | card=A001 | reader=door_1 | action=unlock | reason=ok
```

## Example Card Record

```json
{
  "card_id": "A001",
  "holder": "Han Dhunna",
  "role": "admin",
  "status": "active",
  "allowed_doors": ["door_1", "lobby", "lab_1"],
  "payment": {
    "wallet_linked": true,
    "wallet_provider": "stripe",
    "payment_tokens": []
  },
  "biometric": {
    "fingerprint_enrolled": true,
    "fingerprint_hash": "sha256$...",
    "requires_card_pin": false
  }
}
```

Payment and biometric fields are included as future-facing data structures. The current MVP only uses card identity, status, role, readers, permissions, and events.

## Product Roadmap

### Phase 1: Access Control MVP

Build a reliable card and reader system for private spaces, events, and small businesses.

- clean backend API
- database-backed cards, readers, users, roles, and logs
- owner dashboard
- physical NFC reader prototype
- activate, revoke, and edit cards
- reader-specific actions

### Phase 2: Programmable Experiences

Expand beyond door access into custom interactions.

- event check-ins
- guest passes
- temporary cards
- activity/game triggers
- room or equipment access
- internal credits or tokens

### Phase 3: Commercial Product

Package the system into something sellable.

- hosted dashboard
- onboarding flow
- device setup flow
- card ordering and provisioning
- audit logs and exports
- pricing tiers for homes, venues, and businesses

### Phase 4: Wallet and Payment Exploration

Explore payment-style use cases once the access-control product is stable.

Potential future direction:

- default payment method rules
- merchant/category-based routing
- internal balances and spending limits
- issuer/processor integrations

This phase would require proper fintech infrastructure, regulatory review, fraud controls, KYC/AML, and payment network partnerships. It is intentionally not the first build target.

## API Surface

Current endpoints:

- `POST /scan`
- `GET /cards`
- `POST /cards`
- `PATCH /cards/{card_id}`
- `GET /readers`
- `POST /readers`
- `PATCH /readers/{reader_id}`
- `GET /events`
- `GET /health`

## Status

Early MVP. The core access-control loop now works through an API, database, and dashboard. The next serious step is to connect a real NFC reader device to `POST /scan`.
