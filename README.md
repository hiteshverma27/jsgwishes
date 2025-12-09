JSG Wishes — automated WhatsApp birthday & anniversary sender

Overview
- Read members from Google Sheets.
- Generate personalized images using Pillow templates.
- Upload media and send messages via WhatsApp Cloud API.

Quickstart
1. Copy `.env.example` to `.env` and fill in values.
2. Place `google-service-account.json` in the repo root (or set path in `.env`).
3. Add fonts in `fonts/`, templates in `templates/`, and member photos in `photos/`.
4. Install dependencies: `pip install -r requirements.txt`.
5. Run a dry-run: `python -m src.daily_wishes --dry-run` (dry-run mode implemented to avoid sending messages).

Files
- `src/sheets_client.py` — Google Sheets reader
- `src/image_generator.py` — Creates personalized images
- `src/whatsapp_client.py` — Uploads media and sends WhatsApp messages
- `src/daily_wishes.py` — Main runner (dry-run supported)

Notes
- Keep credentials out of the repo. Use `.env` and `google-service-account.json` kept locally.
- Templates must match the expected sizes and provide space for photo + text.
