# Hotel PMS v2 — /hotelpms

Single-hotel property management system (Larkana market). One deployment = one hotel.

## Live
https://clinic-demo.fastapicloud.dev/hotelpms

## Demo logins
- Owner: `owner@demo.pk` / `demo1234` (full access incl. Settings)
- Staff: PIN `1234` (Ahmed, receptionist — operational screens only, no Settings)

## Modules
Rooms + rack · Reservations · Front desk (check-in/out) · Housekeeping board ·
Restaurant POS-lite (room post / counter cash) · FBR-core billing (SRB 8% card / 15% cash
auto, FBR invoice JSON + QR) · Guest CRM · Reports (occupancy/sales/tax) ·
Marriage-hall events · Owner + staff-PIN auth.
**v2 adds:** Urdu UI toggle (nav ⇄ اردو, RTL) · Inventory/Store (stock, purchase/use,
recipes, auto-deduct on restaurant billing, low-stock alerts) · Payroll-lite
(attendance, monthly salary sheet, paid marking) · 80mm thermal-printer receipts ·
Backup (DB download) + CSV exports (sales/tax/guests) · FBR hardening (3-attempt
retry w/ backoff, per-attempt request/response log, IRN display).

## FBR — honest architecture
- `fbr.py`: builds FBR-format invoice JSON + QR payload, renders QR PNG.
- **TEST MODE default**: invoices get QR + "FBR TEST — not submitted". Nothing is sent.
- LIVE mode: Settings → enter the hotel's OWN IRIS credentials (their signup) +
  API URL → "Submit to FBR" attempts real HTTPS POST **up to 3 times (2s/4s backoff)**,
  every attempt logged to `fbr_log` (request + response), shown on the invoice page
  (attempt history + IRN). submitted / failed shown honestly. Never faked.

## Files
- `db.py` — SQLite schema + demo seed (12 rooms, 3 types, 5 guests, 6 bookings,
  1 active stay w/ folio + restaurant order, 12 menu items, 1 event, 1 hk task,
  15 inventory items, 8 recipes, staff salaries)
- `auth.py` — pbkdf2 owner login + staff PIN, 30-day token sessions
- `fbr.py` — invoice builder, QR, submission (retry + logging)
- `i18n.py` — EN/UR UI strings (Urdu fallback = English, never blank)
- `routes.py` — all pages (server-rendered HTML, print CSS for invoices)

## Notes
- Container SQLite wipes on deploy → seed re-runs automatically on empty DB.
- v1 DBs upgrade in place: ALTER TABLEs for `users.salary_monthly`, `settings.lang`
  (guarded, idempotent).
- Tax rates configurable in Settings (default 8% card / 15% cash per SRB).
- Urdu toggle: nav language switch or Settings → Language; per-browser cookie +
  hotel default.
- Multi-tenant = v3 (not built).
