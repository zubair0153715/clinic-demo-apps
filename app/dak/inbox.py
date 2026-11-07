"""Dak demo inbox — 8 fictional sample emails, clearly labelled DEMO.

These are invented examples so the triage UI is visible before the
user pastes anything. They are NOT real mail, NOT the user's mail,
and no real person or company is named: senders and companies are
fictional. Dates are fixed (5-7 Nov 2026) so tests are
deterministic. Every category in engine.CATEGORIES is covered.
"""

DEMO_EMAILS = [
    {
        "id": "demo-1",
        "from": "Ayesha Khan <hiring@nexahealth.example>",
        "subject": "Interview invite — Junior Pharmacist, NexaHealth (reply by Friday)",
        "date": "2026-11-07",
        "body": (
            "Dear Zubair,\n\nThank you for applying for the Junior Pharmacist "
            "role at NexaHealth. We would like to invite you for an interview "
            "on Thursday 12 November at 11:00 AM at our Karachi office.\n\n"
            "Please confirm by Friday 13 November and bring your CV and "
            "original degrees. We look forward to meeting you.\n\n"
            "Regards,\nAyesha Khan, HR — NexaHealth"
        ),
    },
    {
        "id": "demo-2",
        "from": "Dr. Sana Mir <s.mir@cityuniversity.example>",
        "subject": "URGENT: Pharmacology assignment deadline moved to tomorrow",
        "date": "2026-11-07",
        "body": (
            "Dear students,\n\nThis is urgent. The Pharmacology assignment "
            "deadline has moved to tomorrow (8 November) at 5:00 PM. Please "
            "submit on the portal. Late submissions will lose 10 marks per day.\n\n"
            "Please confirm you have read this email.\n\nDr. Sana Mir"
        ),
    },
    {
        "id": "demo-3",
        "from": "Bilal Ahmed <bilal@techhub.example>",
        "subject": "Re: Project call — can we meet at 2:30 AM?",
        "date": "2026-11-06",
        "body": (
            "Hi,\n\nCan we meet for a project call at 2:30 AM tomorrow? I know "
            "it is late but the client is in another timezone. Please confirm "
            "if that works for you.\n\nThanks,\nBilal"
        ),
    },
    {
        "id": "demo-4",
        "from": "MediSupply <billing@medisupply.example>",
        "subject": "Invoice #INV-2041 — Rs. 48,500 due by 10 Nov",
        "date": "2026-11-06",
        "body": (
            "Dear Customer,\n\nYour invoice #INV-2041 for Rs. 48,500 is due by "
            "10 November 2026. Please transfer to our bank account and share "
            "the receipt. Late payment carries a 2% monthly charge.\n\n"
            "Regards,\nMediSupply Billing"
        ),
    },
    {
        "id": "demo-5",
        "from": "StyleKart <offers@stylekart.example>",
        "subject": "50% OFF Winter Sale ends Sunday — shop now!",
        "date": "2026-11-05",
        "body": (
            "Big Winter Sale! 50% off everything, ends Sunday. Shop now and "
            "use code WINTER50 at checkout.\n\nUnsubscribe here | View in browser\n\n"
            "StyleKart — fashion for everyone."
        ),
    },
    {
        "id": "demo-6",
        "from": "SecureMail <no-reply@securemail.example>",
        "subject": "Security alert: new sign-in from an unknown device",
        "date": "2026-11-07",
        "body": (
            "Hello,\n\nWe noticed a new sign-in to your account from an unknown "
            "device in Lahore. If this was you, no action is needed. If not, "
            "please reset your password immediately and review your recent "
            "activity.\n\nSecureMail Security Team"
        ),
    },
    {
        "id": "demo-7",
        "from": "Hamza Raza <hamza.r@mail.example>",
        "subject": "FYI: library timings changed from next month",
        "date": "2026-11-05",
        "body": (
            "FYI — for your information, the central library will open at "
            "9:00 AM from next month. No action needed, just sharing so you "
            "know.\n\nHamza"
        ),
    },
    {
        "id": "demo-8",
        "from": "Prof. Nadia Ali <n.ali@cityuniversity.example>",
        "subject": "Re: Re: Thesis meeting — notes from last week",
        "date": "2026-11-07",
        "body": (
            "From: Prof. Nadia Ali <n.ali@cityuniversity.example>\n"
            "Sent: 6 November 2026\n\n"
            "Dear Zubair, your thesis outline looks good. Please send the "
            "revised chapter 2 by next week.\n\n"
            "-----Original Message-----\n"
            "From: Zubair Ali\nSent: 5 November 2026\n\n"
            "Dear Prof. Nadia, please find my thesis outline attached for "
            "your review. Could you please review it when you have time?\n\n"
            "-----Original Message-----\n"
            "From: Prof. Nadia Ali\nSent: 3 November 2026\n\n"
            "Dear Zubair, please send your thesis outline before Friday so "
            "we can discuss it in the meeting."
        ),
    },
]


def validate_inbox():
    """Validate the demo inbox. Returns a list of errors."""
    from . import engine

    errors = []
    seen = set()
    for mail in DEMO_EMAILS:
        mid = mail.get("id", "?")
        if mid in seen:
            errors.append(f"demo {mid}: duplicate id")
        seen.add(mid)
        for field in ("id", "from", "subject", "date", "body"):
            if not mail.get(field):
                errors.append(f"demo {mid}: missing {field}")
        if mail.get("date", "")[:4] != "2026":
            errors.append(f"demo {mid}: date not in 2026")
    cats = {engine.classify_category(m["subject"], m["body"])
            for m in DEMO_EMAILS}
    for needed in ("jobs", "study", "meetings", "finance",
                   "promotions", "security", "general"):
        if needed not in cats:
            errors.append(f"demo inbox: no {needed} email")
    return errors
