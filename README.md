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

## Current Prototype

This repository currently contains a Python CLI simulation of the core authorisation logic.

It supports:

- card data stored in JSON
- active and inactive card status checks
- role-based access policies
- card-specific door permissions
- unknown card and unknown reader handling
- event logging to CSV
- simple command-line simulation of card scans and reader selection

This is not yet connected to physical NFC hardware or a web dashboard. Those are planned next.

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
├── code/
│   ├── reader.py              # CLI prototype for card scanning and authorisation
│   └── cardData/
│       ├── cards.json         # Sample card database
│       └── DataInfo.txt       # Card data schema notes
├── docs/
│   └── ROADMAP.md             # Product and engineering roadmap
├── .gitignore
└── README.md
```

## Run Locally

Requires Python 3.10+.

```bash
python code/reader.py
```

Useful commands inside the CLI:

```text
scan A001       # simulate tapping card A001
door door_1     # change the active reader/door
reload          # reload card data from cards.json
help            # show commands
exit            # quit
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

Payment and biometric fields are included as future-facing data structures. The current prototype only uses card identity, status, role, and door permissions.

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

## Status

Early prototype. The core access-control logic exists as a CLI simulation. The next serious step is to turn this into a backend API with a database and connect it to a physical NFC reader.

