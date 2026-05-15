# Roadmap

This project should stay focused on a realistic access-control product before moving into banking or payment routing.

## Immediate Priorities

1. Make the current prototype clean and demonstrable.
2. Replace the CLI-only flow with a small backend API.
3. Store cards, readers, rules, and events in a real database.
4. Build a simple owner dashboard.
5. Connect one real NFC reader and prove the full tap-to-action loop.

## Recommended Build Order

### 1. Backend API

Use FastAPI.

Core endpoints:

- `POST /scan`
- `GET /cards`
- `POST /cards`
- `PATCH /cards/{card_id}`
- `GET /readers`
- `POST /readers`
- `GET /events`

The important endpoint is `POST /scan`: it receives `card_id` and `reader_id`, evaluates the rules, logs the event, and returns an action.

### 2. Database

Start with SQLite for local development, then move to PostgreSQL or Supabase.

Core tables:

- `cards`
- `readers`
- `card_permissions`
- `events`
- `users`
- `organisations`

### 3. Dashboard

Build a simple web dashboard for owners.

Views:

- cards
- readers
- permissions
- event logs
- card activation/revocation

### 4. Hardware Prototype

Start simple:

- NFC card/tag
- PN532 NFC reader or similar
- Raspberry Pi or ESP32
- backend call on tap
- LED/buzzer response for allowed/denied

### 5. Product Packaging

Once the loop works:

- define a target customer
- create a demo video
- build a landing page
- test with one real venue/home/event setup
- collect feedback before adding complex features

## What Not To Build Yet

Do not start with bank-card replacement or payment routing.

That idea is interesting, but it involves regulated financial infrastructure, payment processor partnerships, fraud handling, and compliance. Build the programmable access platform first, then use that traction to justify a deeper fintech product later.

## Best First Commercial Positioning

Programmable NFC cards for private access and custom venue experiences.

Likely early customers:

- private homes
- event organisers
- private members clubs
- escape rooms
- gyms and studios
- rental/Airbnb operators
- small offices
- construction or site access managers

