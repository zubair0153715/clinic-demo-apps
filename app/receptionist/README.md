# AI Receptionist for Clinics — `/receptionist`

24/7 AI receptionist demo for Zubair's agency core offer (setup **$900** + **$500/mo**).
Provider-agnostic conversation engine (works on the `demo` provider today, real
Meta WhatsApp Cloud API when the clinic connects credentials).

## What it does

- **Conversation engine** (`engine.py`): pure state machine, bilingual **EN/AR**
  - Intents: greeting, book, reschedule, cancel, hours, price, location,
    services list, human handoff, fallback
  - Booking flow: service → day → time → name → phone → confirmation → lead
  - Day parsing: today/tomorrow, weekday names EN+AR, DD/MM; time: HH:MM or
    morning/afternoon/evening
  - Human handoff → lead flagged for staff + notification stub through the
    WhatsApp provider abstraction
- **Web demo simulator** (`/receptionist/demo`): WhatsApp-style chat widget —
  this is the sales tool. EN/AR toggle, quick replies.
- **Lead inbox** (`/receptionist/inbox?key=...`): unlisted, owner-only. Leads with
  transcript view + CSV export.

## Honest wiring (read before demoing)

- This page **simulates** WhatsApp. Messages are processed by the real
  conversation engine, but nothing goes over the WhatsApp network.
- Going live for a real clinic requires the clinic's **Meta WhatsApp Cloud API**
  credentials (`SAAS_WHATSAPP_PROVIDER=meta`, `SAAS_WHATSAPP_TOKEN`,
  `SAAS_WHATSAPP_PHONE_NUMBER_ID`). The clinic owner connects these in the
  FastAPI Cloud dashboard — we never ask for passwords (standing rule).
- Never claim the demo sends real WhatsApp messages.

## Admin key

Set `RECEPTIONIST_ADMIN_KEY` in the FastAPI Cloud dashboard (secret env var).
The inbox is 403 without it. Same pattern as `APK_AUDIT_ADMIN_KEY`.

## Persistence note

Leads live in `app/data/receptionist.db` (SQLite). The container can wipe this
on deploy — acceptable for a sales demo. Production: point
`RECEPTIONIST_DB_PATH` at durable storage and/or forward leads to the clinic's
sheet/CRM on capture.

## Legal-use note

Demo clinic ("Pearl Smile Dental") is fictional sample data for the sales demo.
Real deployments are configured per clinic with their own treatments/prices.
