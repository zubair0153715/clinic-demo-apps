"""Sukoon sleep stories — 100% original text, written for this app.

No adapted books, no public-domain retellings, no celebrity
narration. Each story is slow, gentle and ends in sleep. Word
counts are checked by the tests (EN ~350-600 words each, Roman-Urdu
and Urdu versions shorter retellings of the same story).
"""

STORIES = [
    {
        "id": "lantern",
        "title_en": "The Lantern Keeper of the Indus",
        "title_roman": "Darya-e-Sindh ka Chiragh-Wala",
        "title_ur": "دریائے سندھ کا چراغ والا",
        "theme": "river, lamps, dusk",
        "en": (
            "Every evening, just as the sun began to sink behind the low hills, "
            "old Rahim picked up his brass lantern and walked down to the river. "
            "He had done this for forty years, and the river knew his footsteps "
            "the way an old friend knows a voice.\n\n"
            "The path was soft with dust. On either side, the reeds whispered "
            "when the evening breeze passed through them, a sound like paper "
            "being folded very slowly. Rahim walked without hurrying. There was "
            "no need to hurry. The lamps would wait, and the river would wait, "
            "and the night would arrive exactly when it was meant to.\n\n"
            "At the first lamp post he stopped, lifted the little glass door, "
            "and touched the flame to the wick. The light came alive gently, "
            "like a small sun waking up. Then the second lamp, and the third, "
            "each one joining the row until the whole bank of the river glowed "
            "like a string of quiet stars that had decided to rest on the earth "
            "for a while.\n\n"
            "The fishermen were pulling in their boats. One of them, a young "
            "man with tired eyes, called out, \"Chacha, the river is calm "
            "tonight.\" Rahim nodded. \"The river is always calm,\" he said, "
            "\"when we stop trying to hurry it.\" The young man laughed softly "
            "and went home to his supper, and the sound of his oars faded into "
            "the dark water.\n\n"
            "When all twelve lamps were lit, Rahim sat on the flat stone where "
            "he always sat. The river moved past him, slow and wide, carrying "
            "the reflections of the lamps like golden threads. Somewhere far "
            "away a night bird called once, and then was quiet. The air smelled "
            "of cool water and dry grass.\n\n"
            "He thought about nothing in particular. That was the best part of "
            "the evening — the hour when there was nothing left to do, and "
            "nothing left to prove. The lamps were lit. The river was calm. "
            "The night had come, soft as a blanket, and it was enough.\n\n"
            "Slowly, his eyes grew heavy. The lanterns blurred into soft "
            "circles of gold. The river sang its low, endless song. And old "
            "Rahim, the keeper of the lights, drifted into sleep beside the "
            "water, while the twelve small suns kept watch over the river "
            "until morning."
        ),
        "roman": (
            "Har shaam, jab suraj pahariyon ke peeche doobne lagta, buddha Rahim "
            "apni peetal ki laltain uthata aur darya ki taraf chal parta. Chalees "
            "saal se woh yahi kar raha tha, aur darya uske qadmon ko is tarah "
            "pehchanta tha jaise purana dost awaz pehchan le.\n\n"
            "Rasta narm mitti ka tha. Dono taraf sar-kande shaam ki hawa me "
            "sarsarahte, aisi awaz jaise koi kagaz bohat aahista mor raha ho. "
            "Rahim jaldi nahi karta tha. Jaldi ki koi zaroorat nahi thi. Chiragh "
            "intezar karenge, darya intezar karega, aur raat bilkul apne waqt "
            "par aayegi.\n\n"
            "Pehle khambe par woh ruka, chhota sa shishe ka darwaza khola, aur "
            "batti ko aag lagayi. Roshni aahista se jaag uthi, jaise koi chhota "
            "sa suraj. Phir dusra chiragh, teesra, yahan tak ke darya ka kinara "
            "sitaron ki ek khamosh lari ki tarah chamakne laga.\n\n"
            "Jab barah chiragh jal gaye, Rahim usi chapte pathar par baith gaya "
            "jahan woh hamesha baithta tha. Darya uske samne se aahista behta "
            "raha, chiraghon ki roshni ko sunehri dhagon ki tarah le kar. Kahin "
            "door ek raat ka parinda ek dafa bola, phir khamosh ho gaya. Hawa "
            "me thande pani aur sookhi ghaas ki khushboo thi.\n\n"
            "Usne kuch khaas nahi socha. Shaam ka yahi sab se acha hissa tha — "
            "woh ghari jab karne ko kuch baaki nahi, aur sabit karne ko kuch "
            "nahi. Chiragh jal gaye. Darya sakin tha. Raat kambal ki tarah "
            "narm aayi thi, aur yahi kaafi tha.\n\n"
            "Aahista aahista uski aankhein bhaari hone lagi. Chiragh sunehri "
            "halqon me dhundla gaye. Darya apna halka sa, kabhi na khatam hone "
            "wala geet gata raha. Aur buddha Rahim, roshni ka rakhwala, pani "
            "ke kinare neend me doob gaya, jab ke barah chhote suraj subah "
            "tak darya ki rakhwali karte rahe."
        ),
        "ur": (
            "ہر شام، جب سورج پہاڑیوں کے پیچھے ڈوبنے لگتا، بوڑھا رحیم اپنی "
            "پیتل کی لالٹین اٹھاتا اور دریا کی طرف چل پڑتا۔ چالیس سال سے "
            "وہ یہی کر رہا تھا، اور دریا اس کے قدموں کو اس طرح پہچانتا تھا "
            "جیسے پرانا دوست آواز پہچان لے۔\n\n"
            "راستہ نرم مٹی کا تھا۔ دونوں طرف سرکنڈے شام کی ہوا میں سرسراتے، "
            "ایسی آواز جیسے کوئی کاغذ بہت آہستہ موڑ رہا ہو۔ رحیم جلدی نہیں "
            "کرتا تھا۔ جلدی کی کوئی ضرورت نہیں تھی۔\n\n"
            "جب بارہ چراغ جل گئے، رحیم اسی چپٹے پتھر پر بیٹھ گیا جہاں وہ "
            "ہمیشہ بیٹھتا تھا۔ دریا اس کے سامنے سے آہستہ بہتا رہا، چراغوں "
            "کی روشنی کو سنہری دھاگوں کی طرح لے کر۔ ہوا میں ٹھنڈے پانی اور "
            "سوکھی گھاس کی خوشبو تھی۔\n\n"
            "آہستہ آہستہ اس کی آنکھیں بھاری ہونے لگیں۔ چراغ سنہری حلقوں "
            "میں دھندلا گئے۔ دریا اپنا ہلکا سا، کبھی نہ ختم ہونے والا گیت "
            "گاتا رہا۔ اور بوڑھا رحیم، روشنی کا رکھوالا، پانی کے کنارے "
            "نیند میں ڈوب گیا، جب کہ بارہ چھوٹے سورج صبح تک دریا کی "
            "رکھوالی کرتے رہے۔"
        ),
    },
    {
        "id": "train",
        "title_en": "The Slow Train to the Hills",
        "title_roman": "Paharon ki Taraf Slow Train",
        "title_ur": "پہاڑوں کی طرف سلو ٹرین",
        "theme": "train, night journey, mountains",
        "en": (
            "The train left the station at nine, exactly when the station "
            "clock said it would, and for once nobody on the platform was "
            "in a hurry. The passengers climbed aboard slowly, found their "
            "berths, and settled in like people who had all the time in "
            "the world — because on this train, they did.\n\n"
            "Sara took the window berth. The train pulled away with a soft "
            "sigh, and the town slid past her window: lit windows, a "
            "sleeping dog curled on a doorstep, a man closing his shop "
            "shutter for the night. Then the town was gone, and there were "
            "only fields, dark and wide, under a sky full of patient stars.\n\n"
            "The rhythm of the train was gentle. Click-clack, click-clack, "
            "not fast, not slow — the exact rhythm of a heart at rest. "
            "Sara rested her head against the cool glass and watched the "
            "fields go by. A small river glittered under a bridge. A herd "
            "of buffalo slept standing in a field, dark shapes in darker "
            "darkness.\n\n"
            "At the first small station, the train stopped for five minutes. "
            "An old woman sold hot chai through the window, and the steam "
            "rose in the cold air like a small cloud. Sara wrapped her hands "
            "around the paper cup and sipped slowly. The chai was sweet and "
            "hot, and it warmed her all the way down to her toes.\n\n"
            "After the station, the hills began. The train climbed in long, "
            "lazy curves, and through the window Sara could see pine trees "
            "standing in rows like quiet guards. The air coming through the "
            "crack in the window smelled of pine and cold stone. Somewhere "
            "below, a stream hurried over rocks, but the train did not "
            "hurry. The train knew where it was going.\n\n"
            "Sara pulled the thin blanket up to her chin. The click-clack "
            "went on, steady as a lullaby. Her eyes closed on their own, "
            "the way eyes do when there is nothing left to watch and "
            "everything is safe. The hills rolled on outside, the stars "
            "rolled on above, and the slow train carried her gently "
            "through the night, all the way to morning."
        ),
        "roman": (
            "Train raat nau baje station se chali, bilkul usi waqt jab "
            "station ki ghari ne bataya, aur is dafa platform par koi jaldi "
            "me nahi tha. Musafir aahista se sawaar hue, apni berth dhoondhi, "
            "aur is tarah baith gaye jaise unke paas duniya bhar ka waqt ho — "
            "kyun ke is train me waqt hi waqt tha.\n\n"
            "Sara ne khidki wali berth li. Train halki si aah ke saath chali, "
            "aur sheher uski khidki se guzar gaya: roshan khidkiyan, darwaze "
            "par soya hua kutta, ek aadmi apni dukaan ka shutter band kar "
            "raha tha. Phir sheher khatam ho gaya, aur sirf khet reh gaye, "
            "andhere aur wasee, sitaron bhare aasman ke neeche.\n\n"
            "Train ki awaz narm thi. Tik-tak, tik-tak — na tez, na sust — "
            "bilkul waisi hi jaisi aaram karte dil ki dharkan. Sara ne sar "
            "thande shishe se lagaya aur khet guzarte dekhti rahi. Ek chhoti "
            "si nadi pull ke neeche chamki.\n\n"
            "Pehle chhote station par train paanch minute ruki. Ek budhi "
            "aurat ne khidki se garam chai bechi, aur bhap thandi hawa me "
            "chhote se badal ki tarah uthi. Sara ne kagaz ka cup dono haathon "
            "se pakda aur aahista se piya. Chai meethi aur garam thi.\n\n"
            "Station ke baad pahar shuru ho gaye. Train lambi, sust ghumao "
            "me chadhne lagi, aur khidki se Sara ko cheed ke darakht dikhai "
            "diye, khamosh pehredaron ki tarah khade. Khidki ki darz se aane "
            "wali hawa me cheed aur thande pathar ki khushboo thi.\n\n"
            "Sara ne patli si kambal thoddi tak khench li. Tik-tak jaari rahi, "
            "lori ki tarah barabar. Uski aankhein khud-ba-khud band ho gayin, "
            "jis tarah aankhein band ho jati hain jab dekhne ko kuch baaki na "
            "ho aur sab kuch mehfooz ho. Pahar bahar guzarte rahe, sitare upar "
            "guzarte rahe, aur slow train use narmi se raat bhar le kar subah "
            "tak pahunch gayi."
        ),
        "ur": (
            "ٹرین رات نو بجے اسٹیشن سے چلی، بالکل اسی وقت جب اسٹیشن کی "
            "گھڑی نے بتایا، اور اس دفعہ پلیٹ فارم پر کوئی جلدی میں نہیں تھا۔ "
            "مسافر آہستہ سے سوار ہوئے، اپنی برتھ ڈھونڈھی، اور اس طرح بیٹھ "
            "گئے جیسے ان کے پاس دنیا بھر کا وقت ہو۔\n\n"
            "سارہ نے کھڑکی والی برتھ لی۔ ٹرین ہلکی سی آہ کے ساتھ چلی، اور "
            "شہر اس کی کھڑکی سے گزر گیا: روشن کھڑکیاں، دروازے پر سویا ہوا "
            "کتا، ایک آدمی اپنی دکان کا شٹر بند کر رہا تھا۔ پھر شہر ختم "
            "ہو گیا، اور صرف کھیت رہ گئے، اندھیرے اور وسیع، ستاروں بھرے "
            "آسمان کے نیچے۔\n\n"
            "پہلے چھوٹے اسٹیشن پر ٹرین پانچ منٹ رکی۔ ایک بوڑھی عورت نے "
            "کھڑکی سے گرم چائے بیچی، اور بھاپ ٹھنڈی ہوا میں چھوٹے سے بادل "
            "کی طرح اٹھی۔ سارہ نے کاغذ کا کپ دونوں ہاتھوں سے پکڑا اور "
            "آہستہ سے پیا۔\n\n"
            "اسٹیشن کے بعد پہاڑ شروع ہو گئے۔ ٹرین لمبی، سست گھماؤ میں "
            "چڑھنے لگی، اور کھڑکی سے سارہ کو چیڑ کے درخت دکھائی دیے، "
            "خاموش پہریداروں کی طرح کھڑے۔\n\n"
            "سارہ نے پتلی سی کمبل ٹھوڈی تک کھینچ لی۔ ٹک ٹک جاری رہی، لوری "
            "کی طرح برابر۔ اس کی آنکھیں خود بخود بند ہو گئیں، جس طرح "
            "آنکھیں بند ہو جاتی ہیں جب دیکھنے کو کچھ باقی نہ ہو اور سب "
            "کچھ محفوظ ہو۔"
        ),
    },
    {
        "id": "garden",
        "title_en": "The Garden That Only Woke at Night",
        "title_roman": "Woh Bagh Jo Sirf Raat Ko Jaagta Tha",
        "title_ur": "وہ باغ جو صرف رات کو جاگتا تھا",
        "theme": "garden, moonlight, jasmine",
        "en": (
            "Behind the old house at the end of the lane there was a garden "
            "that nobody tended and nobody owned, and yet every night it "
            "woke up more beautiful than any garden in the town. By day it "
            "looked ordinary — a few trees, a cracked stone path, a dry "
            "fountain. But when the moon rose, the garden opened its eyes.\n\n"
            "Maryam discovered it by accident, on a night when she could "
            "not sleep. She had tried counting, she had tried warm milk, "
            "she had tried staring at the ceiling. Nothing worked. So she "
            "put on her shawl, stepped quietly out of the house, and "
            "followed the smell of jasmine down the lane.\n\n"
            "The garden gate was never locked. It swung open at her touch, "
            "without a sound. Inside, the moonlight lay on the stone path "
            "like spilled milk. Jasmine bushes lined both sides, and their "
            "small white flowers glowed faintly, as if each one held a tiny "
            "piece of the moon. The air was sweet enough to drink.\n\n"
            "Maryam walked slowly down the path. A nightingale sang from "
            "the old mango tree — not loudly, not proudly, but softly, the "
            "way you hum to a child who is almost asleep. The dry fountain "
            "in the middle of the garden had a little water in it tonight, "
            "left over from the afternoon rain, and it caught the moonlight "
            "and threw it back in silver pieces.\n\n"
            "She sat on the edge of the fountain and listened. The garden "
            "was full of small sounds: a leaf settling, a moth brushing a "
            "petal, water dripping once, twice, from a jasmine branch. "
            "None of the sounds asked anything of her. None of them needed "
            "an answer. They were just there, like a slow song with no "
            "words.\n\n"
            "Maryam felt her shoulders drop. She had not noticed they were "
            "up around her ears all day. Her breathing slowed without her "
            "trying. The night air was cool on her face, and the jasmine "
            "smell wrapped around her like a second shawl.\n\n"
            "She did not know how long she sat there. Time in the garden "
            "moved the way water moves — slowly, and without asking "
            "permission. When her eyes finally closed, she was still "
            "sitting by the fountain, and the nightingale was still "
            "singing, and the moon was still pouring its quiet light over "
            "the garden that only woke at night."
        ),
        "roman": (
            "Gali ke aakhir me purane ghar ke peeche ek bagh tha jise koi "
            "nahi sambhalta tha aur koi nahi rakhta tha, aur phir bhi har "
            "raat woh sheher ke kisi bhi bagh se zyada khoobsurat jaag uthta "
            "tha. Din me woh aam lagta tha — chand darakht, toota hua pathar "
            "ka rasta, ek sookha fountain. Lekin jab chaand chadhta, bagh "
            "apni aankhein khol leta.\n\n"
            "Maryam ne use ittefaq se dhoondha, ek aisi raat jab use neend "
            "nahi aa rahi thi. Usne ginne ki koshish ki, garam doodh peeya, "
            "chhat ko ghoorne ki koshish ki. Kuch kaam nahi aaya. To usne "
            "shawl odhi, khamoshi se ghar se nikli, aur chambeli ki khushboo "
            "ke peeche gali me chal pari.\n\n"
            "Bagh ka darwaza kabhi band nahi hota tha. Uske chhoote hi bina "
            "awaz ke khul gaya. Andar, chaandni pathar ke raste par doodh "
            "ki tarah bichi thi. Dono taraf chambeli ki jhariyan thi, aur "
            "unke chhote safed phool halke se chamak rahe the, jaise har "
            "ek me chaand ka chhota sa tukda ho. Hawa itni meethi thi ke "
            "peene ko dil chahe.\n\n"
            "Maryam aahista se raste par chali. Aam ke purane darakht se ek "
            "bulbul ga rahi thi — na zor se, na fakhar se, balkay narmi se, "
            "jis tarah aap us bachche ko gungunate hain jo sone wala ho. "
            "Bagh ke beech wale sookhe fountain me aaj thoda sa pani tha, "
            "dopahar ki baarish ka bacha hua, aur usne chaandni ko pakad kar "
            "chaandi ke tukdon me wapas phenk diya.\n\n"
            "Woh fountain ke kinare baith gayi aur sunne lagi. Bagh chhoti "
            "chhoti awazon se bhara tha: ek patta girna, ek parwana phool "
            "ko chhoona, chambeli ki tehni se pani ka ek qatra, phir dusra. "
            "Kisi awaz ne us se kuch nahi manga. Kisi ko jawab nahi chahiye "
            "tha. Woh bas wahan thin, ek aahista geet ki tarah jis ke koi "
            "bol nahi.\n\n"
            "Maryam ne mehsoos kiya ke uske kandhe neeche gir gaye. Usne "
            "ghaur nahi kiya tha ke woh sara din uske kanon ke paas uthe "
            "hue the. Uski saans bina koshish ke aahista ho gayi. Raat ki "
            "hawa uske chehre par thandi thi, aur chambeli ki khushboo "
            "dusri shawl ki tarah uske gird lipat gayi.\n\n"
            "Use nahi pata woh wahan kitni der baithi rahi. Bagh me waqt "
            "us tarah behta tha jis tarah pani behta hai — aahista, aur "
            "bina ijaazat mange. Jab uski aankhein aakhir me band huin, woh "
            "abhi fountain ke kinare baithi thi, aur bulbul abhi ga rahi "
            "thi, aur chaand abhi apni khamosh roshni us bagh par barsa "
            "raha tha jo sirf raat ko jaagta tha."
        ),
        "ur": (
            "گلی کے آخر میں پرانے گھر کے پیچھے ایک باغ تھا جسے کوئی نہیں "
            "سنبھالتا تھا اور کوئی نہیں رکھتا تھا، اور پھر بھی ہر رات وہ "
            "شہر کے کسی بھی باغ سے زیادہ خوبصورت جاگ اٹھتا تھا۔ دن میں وہ "
            "عام لگتا تھا — چند درخت، ٹوٹا ہوا پتھر کا راستہ، ایک سوکھا "
            "فوارہ۔ لیکن جب چاند چڑھتا، باغ اپنی آنکھیں کھول لیتا۔\n\n"
            "مریم نے اسے اتفاق سے ڈھونڈھا، ایک ایسی رات جب اسے نیند نہیں "
            "آ رہی تھی۔ اس نے گننے کی کوشش کی، گرم دودھ پیا، چھت کو گھورنے "
            "کی کوشش کی۔ کچھ کام نہیں آیا۔ تو اس نے شال اوڑھی، خاموشی سے "
            "گھر سے نکلی، اور چنبیلی کی خوشبو کے پیچھے گلی میں چل پڑی۔\n\n"
            "باغ کا دروازہ کبھی بند نہیں ہوتا تھا۔ اس کے چھوتے ہی بغیر آواز "
            "کے کھل گیا۔ اندر، چاندنی پتھر کے راستے پر دودھ کی طرح بچھّی "
            "تھی۔ دونوں طرف چنبیلی کی جھاڑیاں تھیں، اور ان کے چھوٹے سفید "
            "پھول ہلکے سے چمک رہے تھے۔\n\n"
            "وہ فوارے کے کنارے بیٹھ گئی اور سننے لگی۔ باغ چھوٹی چھوٹی "
            "آوازوں سے بھرا تھا: ایک پتّہ گرنا، ایک پروانہ پھول کو چھونا، "
            "چنبیلی کی ٹہنی سے پانی کا ایک قطرہ، پھر دوسرا۔ کسی آواز نے اس "
            "سے کچھ نہیں مانگا۔\n\n"
            "مریم نے محسوس کیا کہ اس کے کندھے نیچے گر گئے۔ اس نے غور نہیں "
            "کیا تھا کہ وہ سارا دن اس کے کانوں کے پاس اٹھے ہوئے تھے۔ اس "
            "کی سانس بغیر کوشش کے آہستہ ہو گئی۔\n\n"
            "اسے نہیں پتا وہ وہاں کتنی دیر بیٹھی رہی۔ باغ میں وقت اس طرح "
            "بہتا تھا جس طرح پانی بہتا ہے — آہستہ، اور بغیر اجازت مانگے۔ "
            "جب اس کی آنکھیں آخر میں بند ہوئیں، وہ ابھی فوارے کے کنارے "
            "بیٹھی تھی، اور بلبل ابھی گا رہی تھی۔"
        ),
    },
]


def validate_stories():
    """Check the bundled stories: ids unique, all 3 languages present,
    EN 300+ words, Roman 200+, Urdu 150+, no brand names, no links."""
    errors = []
    seen = set()
    for s in STORIES:
        if s["id"] in seen:
            errors.append(f"duplicate id {s['id']}")
        seen.add(s["id"])
        for key in ("en", "roman", "ur"):
            if not s.get(key) or not s[key].strip():
                errors.append(f"{s['id']}: {key} missing")
        for key in ("title_en", "title_roman", "title_ur"):
            if not s.get(key):
                errors.append(f"{s['id']}: {key} missing")
        if s.get("en") and len(s["en"].split()) < 300:
            errors.append(f"{s['id']}: EN too short ({len(s['en'].split())}w)")
        if s.get("roman") and len(s["roman"].split()) < 200:
            errors.append(f"{s['id']}: Roman too short ({len(s['roman'].split())}w)")
        if s.get("ur") and len(s["ur"].split()) < 120:
            errors.append(f"{s['id']}: Urdu too short ({len(s['ur'].split())}w)")
        blob = " ".join(s[k] for k in ("en", "roman", "ur") if s.get(k)).lower()
        if "http" in blob or "calm premium" in blob or "headspace" in blob:
            errors.append(f"{s['id']}: brand/link leak")
    return errors


def story_meta():
    """Light metadata for the API (no full text in the list)."""
    from .engine import word_count, reading_minutes
    out = []
    for s in STORIES:
        out.append({
            "id": s["id"],
            "title_en": s["title_en"],
            "title_roman": s["title_roman"],
            "title_ur": s["title_ur"],
            "theme": s["theme"],
            "words_en": word_count(s["en"]),
            "minutes_en": reading_minutes(s["en"]),
            "words_roman": word_count(s["roman"]),
            "minutes_roman": reading_minutes(s["roman"]),
            "words_ur": word_count(s["ur"]),
            "minutes_ur": reading_minutes(s["ur"]),
        })
    return out
