#!/usr/bin/env python3
"""Generate the natural Macedonian pronunciation audio the study guide plays.

The site (index.html) plays pre-recorded clips from the audio/ folder instead
of the browser's built-in speech, so pronunciation is correct and identical on
every device. This script (re)generates those clips via ElevenLabs.

WHEN TO RUN IT: after you add new Macedonian words to index.html, add them to
the lists below and run this to create their audio.

HOW TO RUN IT:
  1. Get a free ElevenLabs API key (elevenlabs.io -> API Keys). The key only
     needs the "Text to Speech" permission.
  2. In Terminal, from this folder:
         export ELEVEN_API_KEY='sk_your_key_here'
         python3 generate_audio.py
  3. It writes audio/<id>.mp3 files + audio/manifest.json, then prints a block
     of JavaScript to paste over the AUDIO_MAP = {...} line in index.html.
  4. Delete/regenerate your API key afterwards.

Existing clips are skipped, so re-running only fetches new words (cheap).
"""
import hashlib, json, os, sys, time, urllib.request, urllib.error

# Fix the common macOS "certificate verify failed" error automatically.
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass

API = os.environ.get("ELEVEN_API_KEY", "").strip()
if not API:
    sys.exit("ERROR: set ELEVEN_API_KEY first, e.g.  export ELEVEN_API_KEY='sk_...'")

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "audio"
MODEL = "eleven_multilingual_v2"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Every Macedonian string the guide speaks ──
ALPHABET = ["авион","баба","воз","град","дом","ѓеврек","еден","жаба","заб","ѕид",
    "Иво","јога","кафе","лав","љубов","мама","небо","њоки","око","пазар","река",
    "сон","таа","куќа","уво","хотел","сонце","чај","џуџе","што"]
NUMBER_WORDS = ["Еден","Една","Едно","Два","Две","Три","Четири","Пет","Шест",
    "Седум","Осум","Девет","Десет"]
NUMBER_SENTENCES = ["Има четири чаши.","Има три мачки.","Има пет кучиња.",
    "Има девет шишиња.","Има десет пенкала."]
QUIZ_VOCAB = ["мачка","куче","кафе","книга","музика","пица","пиво","вино",
    "ресторан","баба","мама","дом","град","река","небо","море","сонце","вода",
    "леб","парк"]
QUIZ_PLURALS = ["мачки","кучиња","кафиња","пенкала","мориња","шишиња","песни",
    "чаши","мачиња"]
QUIZ_VERBS = ["пијам","чита","готвиме","шетам","работиш","гледаат","зборувам",
    "живее","учите","оди","сакам","пиеме"]
# Basic Phrases tab — the ♪ Listen button on each flashcard.
PHRASES = ["Здраво!","Добро утро!","Добар ден!","Добра вечер!","Добра ноќ!",
    "Пријатно!","Се гледаме!","Имај убав ден!","Како си?","Како сте?",
    "Добро сум, благодарам.","Одлично, благодарам!","А, ти?","А, вие?","Благодарам!",
    "Фала!","Нема на што!","Извини!","Извинете!","Нема проблем!","Те молам!","Ве молам!",
    "Како се викаш?","Се викам...","Јас сум...","Мило ми е!","Од каде си?","Јас сум од...",
    "Каде живееш?","Живеам во...","Од кој град си?","Што?","Зошто?","Како?","Кој?","Кога?","Каде?"]
# Nouns tab — singular (front) and plural (back) of every flashcard.
NOUN_SINGULARS = ["стол","град","парк","стан","дом","воз","леб","ресторан","телефон",
    "студент","пазар","хотел","театар","маж","мачка","книга","куќа","маса","зграда","кола",
    "река","вода","жена","чаша","пица","улица","планина","пенкало","кино","село","езеро",
    "море","куче","кафе","шише","маче","дете","око","уво"]
NOUN_PLURALS = ["столови","градови","паркови","станови","домови","возови","лебови",
    "ресторани","телефони","студенти","пазари","хотели","театри","мажи","мачки","книги",
    "куќи","маси","згради","коли","реки","води","жени","чаши","пици","улици","планини",
    "пенкала","кина","села","езера","мориња","кучиња","кафиња","шишиња","мачиња","деца","очи","уши"]

seen, words = set(), []
for group in (ALPHABET, NUMBER_WORDS, NUMBER_SENTENCES, QUIZ_VOCAB, QUIZ_PLURALS, QUIZ_VERBS,
              PHRASES, NOUN_SINGULARS, NOUN_PLURALS):
    for w in group:
        if w not in seen:
            seen.add(w); words.append(w)

# Built-in premade voice (usable by any account; needs only TTS permission).
# Sarah — clear, neutral female. Override with VOICE_ID env if desired.
vname = os.environ.get("VOICE_NAME", "Sarah")
vid = os.environ.get("VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
print(f"Voice: {vname} ({vid})  model={MODEL}")
print(f"Generating {len(words)} clips into {OUT_DIR}/ ...")

def tts(text, path):
    body = json.dumps({
        "text": text,
        "model_id": MODEL,
        "voice_settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": True},
    }).encode("utf-8")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128"
    req = urllib.request.Request(url, data=body, method="POST",
        headers={"xi-api-key": API, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=60) as r:
        audio = r.read()
    with open(path, "wb") as f:
        f.write(audio)
    return len(audio)

manifest, fails = {}, []
for i, text in enumerate(words, 1):
    fname = hashlib.md5(text.encode("utf-8")).hexdigest()[:16] + ".mp3"
    path = os.path.join(OUT_DIR, fname)
    manifest[text] = fname
    if os.path.exists(path) and os.path.getsize(path) > 0:
        print(f"  [{i:2}/{len(words)}] skip  {text}")
        continue
    for attempt in range(4):
        try:
            n = tts(text, path)
            print(f"  [{i:2}/{len(words)}] ok  {text} -> {fname} ({n}B)")
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:200]
            print(f"  [{i:2}/{len(words)}] HTTP {e.code} attempt {attempt+1}: {msg}")
            if e.code in (401, 403):
                sys.exit("Auth failed — check the API key.")
            time.sleep(3 * (attempt + 1))
        except Exception as e:
            print(f"  [{i:2}/{len(words)}] err attempt {attempt+1}: {e}")
            time.sleep(3 * (attempt + 1))
    else:
        del manifest[text]; fails.append(text)

with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
print(f"\nDone. {len(manifest)} clips written. Failures: {fails or 'none'}")

# Print the exact line to paste into index.html so the site knows the new files.
compact = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))
print("\n" + "=" * 60)
print("Copy the line below and replace the 'const AUDIO_MAP = {...};'")
print("line in index.html with it:\n")
print(f"  const AUDIO_MAP = {compact};")
print("=" * 60)
