# Face Watchlist Recognition System

A prototype system that watches a camera feed, compares detected faces against
a "wanted" watchlist, and alerts when a match is found. Unrecognized faces are
ignored — no alert is triggered for anyone not on the list.

## How it works

1. `enroll.py` builds a database (`watchlist.pkl`) of face embeddings from photos
   in `wanted_photos/`.
2. `main.py` runs the live camera, detects faces, computes their embeddings, and
   compares each one to the watchlist using cosine similarity.
3. If similarity crosses `SIMILARITY_THRESHOLD` (see `config.py`), an alert fires:
   an annotated snapshot is saved, a CSV log entry is written, and (optionally)
   a Telegram message or email is sent.
4. `evaluate.py` measures precision/recall on a held-out test set — useful for
   proving the system's accuracy in a report or presentation.

## Project structure

```
face_watchlist/
├── config.py            <- all settings live here
├── enroll.py             <- builds the watchlist database
├── main.py                <- live camera matching + alerting
├── evaluate.py            <- precision/recall testing
├── requirements.txt
├── wanted_photos/         <- enrollment photos (see below)
├── test_photos/           <- optional, for evaluate.py
│   ├── known/             <- different photos of enrolled people
│   └── unknown/           <- photos of people NOT on the watchlist
├── alerts/                <- auto-created
│   └── <person_name>/
│       ├── log.csv
│       └── <timestamp>.jpg
└── watchlist.pkl          <- auto-created by enroll.py
```

## Enrolling people

Two supported layouts, can mix both:

- **One photo**: `wanted_photos/john_doe.jpg`
- **Multiple photos** (recommended, more accurate): `wanted_photos/jane_smith/1.jpg`, `2.jpg`, `3.jpg`
  Multiple photos are averaged into one embedding — using a few different
  angles/lighting conditions per person meaningfully improves matching.

Run:
```bash
python enroll.py
```

## Running the live system

```bash
python main.py
```

- **Red box** = match found on watchlist -> alert triggered
- **Green box** = unrecognized face -> ignored, no alert
- Press `q` to quit

## Tuning

All settings are in `config.py`:

| Setting | What it does |
|---|---|
| `SIMILARITY_THRESHOLD` | Higher = stricter matching (fewer false alarms, may miss real matches). Start at 0.50 and adjust based on `evaluate.py` results. |
| `ALERT_COOLDOWN` | Seconds before re-alerting on the same person, to avoid spamming. |
| `CAMERA_INDEX` | Which camera to use if you have more than one. |
| `ENABLE_TELEGRAM` / `ENABLE_EMAIL` | Turn on real-time alert delivery (see below). |

## Enabling real alerts

### Telegram
1. Message `@BotFather` on Telegram -> `/newbot` -> copy the bot token
2. Message `@userinfobot` -> it replies with your chat id
3. In `config.py`, set `ENABLE_TELEGRAM = True` and fill in the token + chat id

### Email
1. If using Gmail, create an app password: https://myaccount.google.com/apppasswords
2. In `config.py`, set `ENABLE_EMAIL = True` and fill in `EMAIL_FROM`, `EMAIL_TO`, `EMAIL_APP_PASSWORD`

## Measuring accuracy

Put a few test photos in `test_photos/known/` (people on the watchlist, but
**different photos** than the ones used to enroll them) and `test_photos/unknown/`
(people not on the watchlist). Then:

```bash
python evaluate.py
```

This prints per-photo results plus precision and recall — real numbers you can
put in a competition report instead of just "it seems to work."

## Limitations / honest disclosure

This is a proof-of-concept, not a production system. For real deployment you'd
also need: liveness/anti-spoofing (to stop someone holding up a photo), GPU
acceleration for multi-camera scale, integration with an actual authorized law
enforcement database, legal/privacy compliance review, and human-in-the-loop
verification before any real-world action is taken on an alert.