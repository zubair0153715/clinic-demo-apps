# LabLink (/lablink)

University lab-connect app for **SMBBMU Larkana — Pharm-D program**: teachers and
students connect in one place.

## Features
- **Auth + roles** — student / teacher / admin (pbkdf2 + token sessions, 30-day cookie).
  Registration with name, role, batch and optional phone.
- **Announcements** — teachers post announcements to a batch or everyone; students
  see a feed and can comment. Announcements also land in the notification center.
- **Experiments Library** — searchable by name / subject / chemical. Each experiment
  has objective, a chemicals table with exact quantities, apparatus, step-by-step
  procedure, precautions, expected observation and a labelled diagram. Teachers/admins
  can add & edit experiments. Seeded with 8 standard Pharm-D practicals (Simple Syrup IP,
  Calamine Lotion IP, Aspirin synthesis, Paracetamol tablets + evaluation, Caffeine
  extraction, Partition coefficient of benzoic acid, Frog heart pharmacology,
  Clove microscopy).
- **Lab Inventory** — searchable chemicals (stock qty, lab, low-stock flag) and
  instruments (working / under maintenance). Staff can update stock and add items.
- **Library** — searchable book catalog (copies total/available, shelf). Students can
  reserve; staff see requests and can issue / mark returned.
- **Timetable + auto-notifications** — weekly lab timetable, a "Today's Labs" view,
  and automatic in-app notifications on the day a batch has a lab (generated
  idempotently — no duplicates). A ready-to-copy **WhatsApp message** for the day's
  schedule is generated on the timetable page.
- **Admin** — manage users (role / activate-deactivate) plus all content CRUD above.

## Demo accounts
| Role    | Email            | Password  |
|---------|------------------|-----------|
| Student | student@demo.pk  | demo1234  |
| Teacher | teacher@demo.pk  | demo1234  |
| Admin   | admin@demo.pk    | demo1234  |

## Honest limits
- **SQLite in the container is wiped on redeploy** — the demo seed (users, 8
  experiments, inventory, 15 books, 12 timetable entries) rebuilds automatically
  on first boot, but user-created data does not survive a redeploy.
- **WhatsApp:** the app prepares a ready-to-copy message; real automatic WhatsApp
  sending requires the university's official WhatsApp Business API and is NOT faked.
- Experiment quantities follow standard textbook/IP practical values as commonly
  taught; teachers should verify against their current practical manual before a
  graded session.
