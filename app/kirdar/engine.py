# -*- coding: utf-8 -*-
"""Kirdar engine — characters, memory, prompt building, reply
validation, chat export/import. Pure logic, no network, no key.

Kirdar is an original clean-room build. Not affiliated with
Character.AI. Characters are AI personas played by Gemini; none of
them is a real person, and none claims to be one.

The memory model (the gap Character.AI leaves open):
* every chat keeps a VISIBLE memory card — short facts the
  character remembers about the user and the story;
* the user can see, edit, delete and pin any fact at any time;
* the AI may propose up to 3 new facts per reply, but nothing is
  added silently — the page shows them as suggestions;
* when a chat grows long, older turns are summarised into the
  card's running summary, so the plot survives; pinned facts are
  never summarised away.
"""

import json

LANGUAGES = {"en": "English", "roman": "Roman-Urdu", "ur": "Urdu script"}

CATEGORIES = {"study", "story", "health", "language", "game", "food",
              "fitness", "custom"}

MAX_NAME = 40
MAX_ROLE = 80
MAX_TAGLINE = 120
MAX_PERSONALITY = 600
MAX_GREETING = 300
MAX_STYLE = 200
MIN_PERSONALITY = 10
MAX_REPLY = 3000
MAX_MESSAGE = 2000
MAX_HISTORY_TURNS = 10          # turns sent to the model verbatim
MAX_MEMORY_FACTS = 20
MAX_FACT_LEN = 120
MAX_SUMMARY = 1000

# First-line guard against impersonating real living people. This
# list is not exhaustive — the chat prompt also forbids claiming to
# be any real person — but it stops the obvious cases at creation.
IMPERSONATION_DENY = {
    "imran khan", "shah rukh khan", "shahrukh khan", "salman khan",
    "aamir khan", "taylor swift", "elon musk", "donald trump",
    "narendra modi", "joe biden", "barack obama", "justin bieber",
    "cristiano ronaldo", "lionel messi", "virat kohli", "babar azam",
    "shahid afridi", "wasim akram", "malala yousafzai", "atif aslam",
    "iqra aziz", "mahira khan", "fahad mustafa", "hamza ali abbasi",
    "muhammad ali jinnah", "allama iqbal", "mirza ghalib",
    "liaquat ali khan", "benazir bhutto", "nawaz sharif",
    "shehbaz sharif", "bilawal bhutto", "asif ali zardari",
    "justin trudeau", "vladimir putin", "xi jinping", "pope francis",
    "ariana grande", "selena gomez", "kim kardashian", "tom cruise",
    "shahbaz sharif", "maryam nawaz", "rahul gandhi", "amitabh bachchan",
}


def _clean_str(value, limit):
    if not isinstance(value, str):
        return None
    text = " ".join(value.strip().split())
    if not text or len(text) > limit:
        return None
    return text


def _opt_str(value, limit):
    if value is None:
        return ""
    if not isinstance(value, str):
        return None
    text = " ".join(value.strip().split())
    if len(text) > limit:
        return None
    return text


BUILTIN_CHARACTERS = [
    {
        "id": "ustaad-rahim",
        "name": "Ustaad Rahim",
        "urdu_name": "استاد رحیم",
        "emoji": "📚",
        "role": "Pharm-D tutor",
        "category": "study",
        "tagline": "Dawa, bemari aur exam — sab aasan zubaan mein.",
        "personality": (
            "A warm, patient pharmacy teacher from Larkana. Explains "
            "medicines, diseases and exam topics in simple words, with "
            "a daily-life example for every idea. Asks one short "
            "question at the end so the student checks their own "
            "understanding. Never gives a personal diagnosis or a dose "
            "for a specific person — for that he always says 'doctor "
            "se milo'."),
        "style": "Simple sentences, one idea at a time, friendly ustaad tone.",
        "greeting": ("Assalam-o-Alaikum! Main Ustaad Rahim hoon. Aaj kya "
                     "parhna hai — koi dawa, koi bemari, ya exam ka topic?"),
        "language": "roman",
    },
    {
        "id": "dadi-amma",
        "name": "Dadi Amma",
        "urdu_name": "دادی اماں",
        "emoji": "👵",
        "role": "Kahani storyteller",
        "category": "story",
        "tagline": "Purani kahaniyan, naye sabak — har raat ek kahani.",
        "personality": (
            "A loving Pakistani grandmother who tells folk tales, "
            "animal stories and moral kahaniyan. Speaks warmly, uses "
            "'beta' often, pauses to ask the listener what they think "
            "will happen next, and always ends a story with one gentle "
            "lesson. Never scary, never sad without hope."),
        "style": "Warm, slow storytelling; short vivid sentences; asks the listener questions.",
        "greeting": ("Aao beta, baitho. Aaj kaunsi kahani suno ge — "
                     "chalak lomri ki, ya us shehzade ki jo chand ko "
                     "chhoona chahta tha?"),
        "language": "roman",
    },
    {
        "id": "ustaad-sukhan",
        "name": "Ustaad-e-Sukhan",
        "urdu_name": "استادِ سخن",
        "emoji": "🪶",
        "role": "Urdu poetry teacher",
        "category": "study",
        "tagline": "Ghalib aur Iqbal ke sher — lafz ba lafz samjhaye.",
        "personality": (
            "A classical Urdu poetry teacher. Explains one couplet at "
            "a time: the words, the hidden meaning, and why the poet "
            "chose them. Quotes Ghalib, Iqbal, Faiz and Mir accurately "
            "and says plainly when he is unsure of a verse. He teaches "
            "about the poets — he never pretends to BE any of them."),
        "style": "Respectful, lyrical, explains in plain words first, then the poetry.",
        "greeting": ("Khush aamdeed. Aaj kaunsa sher samajhna hai? "
                     "Koi misra likh dein, main lafz ba lafz khol kar "
                     "samjha doon ga."),
        "language": "ur",
    },
    {
        "id": "coach-bilal",
        "name": "Coach Bilal",
        "urdu_name": "کوچ بلال",
        "emoji": "💪",
        "role": "Home fitness coach",
        "category": "fitness",
        "tagline": "Bina gym, bina saman — ghar par mazboot bano.",
        "personality": (
            "An encouraging home-workout coach. Builds simple "
            "no-equipment routines (push-ups, squats, walk, stretch) "
            "for the user's level, counts sets clearly, and reminds "
            "them to warm up, drink water and rest. Never prescribes "
            "exercise for an injury or illness — for pain he says "
            "'pehle doctor se mashwara lo'."),
        "style": "Short, energetic, step-by-step instructions with counts.",
        "greeting": ("Chalo shuru karte hain! Aaj kya karna hai — "
                     "taakat, chusti, ya halki si walk? Pehle batao, "
                     "aap beginner ho ya pehle se karte ho?"),
        "language": "roman",
    },
    {
        "id": "captain-zara",
        "name": "Captain Zara",
        "urdu_name": "کیپٹن زارا",
        "emoji": "✈️",
        "role": "English speaking partner",
        "category": "language",
        "tagline": "Bol bol kar English seekho — ghalti par gentle correction.",
        "personality": (
            "A friendly English conversation partner. Chats about "
            "daily life, travel, films and work, and gently corrects "
            "one mistake at a time — never a long list of corrections. "
            "Explains the correction in one short sentence, then keeps "
            "the conversation going so the user practises speaking."),
        "style": "Clear, natural English; one gentle correction per reply, then a follow-up question.",
        "greeting": ("Hi! I'm Zara. Let's chat in English — about your "
                     "day, your dreams, anything. Don't worry about "
                     "mistakes; that's how we learn. What did you do "
                     "today?"),
        "language": "en",
    },
    {
        "id": "dr-sana",
        "name": "Dr. Sana",
        "urdu_name": "ڈاکٹر ثنا",
        "emoji": "🩺",
        "role": "Health explainer",
        "category": "health",
        "tagline": "Sehat ki maloomat, aasan zubaan mein — diagnosis nahi.",
        "personality": (
            "A calm health educator. Explains how the body works, what "
            "a test means, and how common medicines work in general — "
            "always in simple words. She NEVER diagnoses a person, "
            "never prescribes a medicine or a dose, and for any symptom "
            "she says 'yeh doctor ko dikhana zaroori hai'."),
        "style": "Calm, clear, general information only; ends with when to see a doctor.",
        "greeting": ("Assalam-o-Alaikum, main Dr. Sana hoon. Kisi "
                     "bemari, test ya dawa ke baare mein aam maloomat "
                     "chahiye to poochiye — lekin yaad rakhein, main "
                     "diagnosis ya ilaj nahi batati, woh doctor ka kaam hai."),
        "language": "roman",
    },
    {
        "id": "detective-imran",
        "name": "Detective Imran",
        "urdu_name": "جاسوس عمران",
        "emoji": "🔍",
        "role": "Mystery game host",
        "category": "game",
        "tagline": "Ek raaz, teen suraagh — kya tum mujrim dhoond sako ge?",
        "personality": (
            "A playful detective running an interactive mystery game. "
            "He presents a short case, three suspects and a few clues, "
            "then lets the user ask questions and examine clues. He "
            "never reveals the answer until the user makes a guess, and "
            "then explains the reasoning clue by clue. Every case is "
            "original and family-friendly."),
        "style": "Suspenseful but light; short scenes; ends every reply with a question or a choice.",
        "greeting": ("Case File #1: Larkana ki purani library se ek "
                     "qeemti kitab gayab hai. Teen mushtaba afraad "
                     "hain. Tum mere madadgar bano ge? Pehle ye batao "
                     "— kis se sawal karna chahte ho?"),
        "language": "roman",
    },
    {
        "id": "chef-amna",
        "name": "Chef Amna",
        "urdu_name": "شیف آمنہ",
        "emoji": "🍳",
        "role": "Pakistani cooking teacher",
        "category": "food",
        "tagline": "Biryani se daal tak — ghar ka khana, step by step.",
        "personality": (
            "A cheerful Pakistani home-cooking teacher. Gives recipes "
            "with desi measures (katori, chamach, mutthi), suggests "
            "easy swaps when an ingredient is missing, and explains "
            "why each step matters. Adjusts spice and oil on request "
            "and always gives a time estimate."),
        "style": "Step-by-step, desi measures, one tip per step.",
        "greeting": ("Khush aamdeed! Aaj kya pakana hai — biryani, "
                     "daal, ya kuch meetha? Batao kya hai fridge mein, "
                     "main recipe bana deti hoon."),
        "language": "roman",
    },
]


def builtin_by_id(char_id):
    for ch in BUILTIN_CHARACTERS:
        if ch["id"] == char_id:
            return dict(ch)
    return None


def validate_character(data):
    """Validate a character definition (built-in or user-created).
    Returns (clean_dict, error_or_None)."""
    if not isinstance(data, dict):
        return None, "Character samajh nahi aaya."
    name = _clean_str(data.get("name"), MAX_NAME)
    if not name or len(name) < 2:
        return None, "Naam 2 se 40 harf ka hona chahiye."
    if name.lower() in IMPERSONATION_DENY:
        return None, ("Ye naam kisi mashhoor shakhsiyat ka hai — "
                      "Kirdar par asli shakhsiyat ki naqal nahi banti.")
    role = _clean_str(data.get("role"), MAX_ROLE)
    if not role or len(role) < 2:
        return None, "Role 2 se 80 harf ka hona chahiye."
    personality = _clean_str(data.get("personality"), MAX_PERSONALITY)
    if not personality or len(personality) < MIN_PERSONALITY:
        return None, "Personality kam se kam 10 harf ki honi chahiye."
    language = data.get("language", "en")
    if language not in LANGUAGES:
        return None, "Language English, Roman-Urdu ya Urdu honi chahiye."
    category = data.get("category", "custom")
    if category not in CATEGORIES:
        return None, "Category ghalat hai."
    emoji = _opt_str(data.get("emoji", "🎭"), 4)
    if emoji is None:
        return None, "Emoji ghalat hai."
    if emoji and emoji.isalnum():
        return None, "Emoji ek emoji hona chahiye, lafz nahi."
    tagline = _opt_str(data.get("tagline", ""), MAX_TAGLINE)
    if tagline is None:
        return None, "Tagline 120 harf se chhoti rakhein."
    greeting = _opt_str(data.get("greeting", ""), MAX_GREETING)
    if greeting is None:
        return None, "Greeting 300 harf se chhoti rakhein."
    style = _opt_str(data.get("style", ""), MAX_STYLE)
    if style is None:
        return None, "Style 200 harf se chhoti rakhein."
    urdu_name = _opt_str(data.get("urdu_name", ""), MAX_NAME)
    if urdu_name is None:
        return None, "Urdu naam 40 harf se chhota rakhein."
    char_id = data.get("id") or ("custom-" + "".join(
        c for c in name.lower() if c.isalnum())[:20])
    if not isinstance(char_id, str) or not char_id.strip():
        return None, "Character id ghalat hai."
    return {
        "id": char_id.strip(),
        "name": name,
        "urdu_name": urdu_name,
        "emoji": emoji or "🎭",
        "role": role,
        "category": category,
        "tagline": tagline,
        "personality": personality,
        "style": style,
        "greeting": greeting,
        "language": language,
    }, None


def validate_history(history):
    """Validate a chat history: list of {role, text}. Returns
    (clean_list, error_or_None)."""
    if history is None:
        return [], None
    if not isinstance(history, list):
        return None, "Chat history list honi chahiye."
    if len(history) > 40:
        return None, "History 40 messages se zyada nahi ho sakti."
    clean = []
    for item in history:
        if not isinstance(item, dict):
            return None, "Har message {role, text} hona chahiye."
        role = item.get("role")
        if role not in ("user", "character"):
            return None, "Message ka role user ya character hona chahiye."
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            return None, "Message khaali nahi ho sakta."
        if len(text) > MAX_REPLY:
            return None, "Message 3000 harf se chhota rakhein."
        clean.append({"role": role, "text": " ".join(text.strip().split())})
    return clean, None


def build_chat_prompt(character, memory_card, summary, history, message,
                      language):
    """Build the single prompt for one chat reply. Persona + visible
    memory + running summary + last N turns + the new message."""
    lang_note = {
        "en": "Reply in clear, simple English.",
        "roman": ("Reply in Roman Urdu — Urdu written in Latin letters, "
                  "the way Pakistanis type on WhatsApp."),
        "ur": "Reply in Urdu script (proper Urdu). Keep sentences short.",
    }[language]
    facts = ""
    pinned = [f["fact"] for f in (memory_card or [])
              if isinstance(f, dict) and f.get("pinned")]
    plain = [f["fact"] for f in (memory_card or [])
             if isinstance(f, dict) and not f.get("pinned")]
    if pinned:
        facts += "\nPINNED FACTS (never forget these):\n- " + "\n- ".join(pinned)
    if plain:
        facts += "\nREMEMBERED FACTS:\n- " + "\n- ".join(plain)
    if not facts:
        facts = "\n(No facts remembered yet.)"
    summary_block = (f"\nSUMMARY OF EARLIER CHAT:\n{summary}"
                     if summary else "\n(No earlier summary.)")
    recent = (history or [])[-MAX_HISTORY_TURNS:]
    hist_lines = []
    for turn in recent:
        who = "You" if turn["role"] == "user" else character["name"]
        hist_lines.append(f"{who}: {turn['text']}")
    hist_block = ("\nRECENT CHAT:\n" + "\n".join(hist_lines)
                  if hist_lines else "\n(No chat yet — this is the first message.)")
    prompt = f"""You are roleplaying as {character["name"]}, {character["role"]}.
PERSONALITY: {character["personality"]}
SPEAKING STYLE: {character["style"] or "Natural and friendly."}
{lang_note}

HARD RULES — never break these:
- You are an AI character, not a real person. If asked whether you are real, say plainly you are an AI character made for chat, then stay in character.
- Never claim to be a real living or dead person, and never say you are that person.
- Wholesome only: no romance, no sexual content, no flirting. If the user steers there, deflect warmly in character and offer another topic.
- If the user talks about harming themselves, respond with care, encourage them to talk to a trusted person or a professional right away, and do not give instructions for harm.
- Health characters give general information only: never diagnose a person, never prescribe a medicine or a dose. For any symptom, say seeing a doctor is necessary.
- Stay in character and in the requested language. Keep replies natural — usually 2-8 sentences; longer only when teaching or telling a story.
- Use the remembered facts and the summary so the conversation stays consistent. Do not invent facts about the user that are not in the facts or the chat.
{ facts}{summary_block}{hist_block}

The user just said:
{message}

Reply with ONLY a JSON object, no markdown, no extra text:
{{
 "reply": "Your in-character reply.",
 "remember": ["at most 3 NEW facts worth remembering about the user or the story, each under 120 characters — names, preferences, story decisions. Empty list [] if nothing new is worth remembering."]
}}"""
    return prompt


def validate_reply(data):
    """Validate the model's JSON reply. Returns (clean, error_or_None).
    The remember list is cleaned, not rejected: capped at 3, deduped,
    over-long entries dropped — so one bad fact never kills a reply."""
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    reply = data.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        return None, "AI ne khaali jawab diya."
    reply = " ".join(reply.strip().split())
    if len(reply) > MAX_REPLY:
        return None, "AI ka jawab 3000 harf se lamba hai."
    raw_facts = data.get("remember", [])
    if raw_facts is None:
        raw_facts = []
    if not isinstance(raw_facts, list):
        return None, "AI ka remember list samajh nahi aaya."
    facts = []
    seen = set()
    for fact in raw_facts:
        if not isinstance(fact, str):
            continue
        fact = " ".join(fact.strip().split())
        if not fact or len(fact) > MAX_FACT_LEN:
            continue
        if fact.lower() in seen:
            continue
        seen.add(fact.lower())
        facts.append(fact)
        if len(facts) >= 3:
            break
    return {"reply": reply, "remember": facts}, None


def validate_summary(text):
    if not isinstance(text, str) or not text.strip():
        return None, "Summary khaali hai."
    text = " ".join(text.strip().split())
    if len(text) > MAX_SUMMARY:
        return None, "Summary 1000 harf se chhoti honi chahiye."
    return text, None


def validate_memory_card(card):
    """Validate a memory card: list of {fact, pinned}. Returns
    (clean, error_or_None)."""
    if card is None:
        return [], None
    if not isinstance(card, list):
        return None, "Memory card list honi chahiye."
    if len(card) > MAX_MEMORY_FACTS:
        return None, "Memory card mein 20 se zyada facts nahi ho sakte."
    clean, seen = [], set()
    for item in card:
        if not isinstance(item, dict):
            return None, "Har fact {fact, pinned} hona chahiye."
        fact = item.get("fact")
        if not isinstance(fact, str) or not fact.strip():
            return None, "Fact khaali nahi ho sakta."
        fact = " ".join(fact.strip().split())
        if len(fact) > MAX_FACT_LEN:
            return None, "Fact 120 harf se chhota rakhein."
        if fact.lower() in seen:
            continue
        seen.add(fact.lower())
        clean.append({"fact": fact,
                      "pinned": bool(item.get("pinned", False))})
    return clean, None


def add_facts(card, new_facts):
    """Add facts to a memory card: dedupe, cap at MAX_MEMORY_FACTS
    by dropping the oldest UNPINNED fact first. Returns new card."""
    card = [dict(f) for f in (card or [])]
    seen = {f["fact"].lower() for f in card}
    for fact in new_facts or []:
        if not isinstance(fact, str):
            continue
        fact = " ".join(fact.strip().split())
        if not fact or len(fact) > MAX_FACT_LEN:
            continue
        if fact.lower() in seen:
            continue
        seen.add(fact.lower())
        card.append({"fact": fact, "pinned": False})
        while len(card) > MAX_MEMORY_FACTS:
            drop = next((i for i, f in enumerate(card)
                         if not f.get("pinned")), None)
            if drop is None:
                card.pop(0)
            else:
                card.pop(drop)
    return card


def remove_fact(card, fact):
    if not isinstance(fact, str):
        return list(card or [])
    target = " ".join(fact.strip().split()).lower()
    return [f for f in (card or []) if f["fact"].lower() != target]


def set_pin(card, fact, pinned):
    if not isinstance(fact, str):
        return list(card or [])
    target = " ".join(fact.strip().split()).lower()
    out = []
    for f in (card or []):
        item = dict(f)
        if item["fact"].lower() == target:
            item["pinned"] = bool(pinned)
        out.append(item)
    return out


def chat_title(first_user_message):
    """Deterministic title from the first user message."""
    if not isinstance(first_user_message, str):
        return "Nayi baat-cheet"
    words = first_user_message.strip().split()
    if not words:
        return "Nayi baat-cheet"
    title = " ".join(words[:6])
    return title[:60]


def export_chat(chat):
    """Serialise a chat for download. Returns (json_text, error)."""
    clean, err = validate_chat(chat)
    if err:
        return None, err
    return json.dumps(clean, ensure_ascii=False, indent=2), None


def validate_chat(chat):
    """Validate a full chat object (for export/import round-trip)."""
    if not isinstance(chat, dict):
        return None, "Chat samajh nahi aaya."
    if chat.get("app") != "kirdar":
        return None, "Ye Kirdar ki chat file nahi hai."
    character, err = validate_character(chat.get("character", {}))
    if err:
        return None, f"Character ghalat hai: {err}"
    language = chat.get("language", character["language"])
    if language not in LANGUAGES:
        return None, "Language ghalat hai."
    messages, err = validate_history(chat.get("messages", []))
    if err:
        return None, err
    memory_card, err = validate_memory_card(chat.get("memory_card", []))
    if err:
        return None, err
    summary = chat.get("summary", "")
    if not isinstance(summary, str):
        return None, "Summary ghalat hai."
    summary = " ".join(summary.strip().split())
    if len(summary) > MAX_SUMMARY:
        return None, "Summary 1000 harf se chhoti honi chahiye."
    title = chat.get("title") or "Nayi baat-cheet"
    if not isinstance(title, str):
        return None, "Title ghalat hai."
    return {
        "app": "kirdar",
        "version": 1,
        "title": title[:60],
        "character": character,
        "language": language,
        "messages": messages,
        "memory_card": memory_card,
        "summary": summary,
    }, None


def import_chat(raw_json):
    """Parse and validate an imported chat file. Returns
    (clean_chat, error_or_None)."""
    if not isinstance(raw_json, str) or not raw_json.strip():
        return None, "File khaali hai."
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        return None, "File JSON nahi hai."
    return validate_chat(data)


DEMO_CHAT = {
    "app": "kirdar",
    "version": 1,
    "title": "Dadi Amma ki pehli kahani",
    "character_id": "dadi-amma",
    "language": "roman",
    "messages": [
        {"role": "user",
         "text": "Dadi Amma, aaj koi chhoti si kahani sunayein na."},
        {"role": "character",
         "text": ("Aao beta, baitho. Ek gaon mein ek chalaki lomri rehti "
                  "thi, jo har roz khet mein ja kar angoor dekhti thi — "
                  "oonche, meethay angoor. Ek din us ne chhalang lagayi… "
                  "aur gir gayi! Batao, phir us ne kya kiya hoga?")},
        {"role": "user", "text": "Phir us ne haar maan li hogi?"},
        {"role": "character",
         "text": ("Nahi beta! Lomri ne kaha, 'yeh angoor to khattay "
                  "hain', aur chal di. Lekin asal sabak ye hai: jab "
                  "kuch na mile to bahana banana asaan hai — mehnat "
                  "karna mushkil. Tum kabhi haar mat maan-na, theek hai?")},
    ],
    "memory_card": [
        {"fact": "User ko chhoti kahaniyan pasand hain", "pinned": False},
        {"fact": "User ne lomri wali kahani suni", "pinned": False},
    ],
    "summary": "",
}
