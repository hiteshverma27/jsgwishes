You are helping me implement an end-to-end automation system for sending personalized WhatsApp birthday & anniversary wishes using Python, WhatsApp Cloud API, and Google Sheets.

🎯 Goal:
- Every morning at 9 AM automatically:
  1. Read member data from Google Sheets
  2. Identify members whose birthday or anniversary is TODAY
  3. Generate a personalized wish image with their photo, name, designation, group & city
  4. Send that image + caption text via WhatsApp Cloud API to their WhatsApp number
  5. Log success or failure (later phase)

📄 Data Source:
- Google Sheet called "JSG Members"
- Columns (first row is headers):
  id
  name
  designation
  birthdate (YYYY-MM-DD)
  anniversary (YYYY-MM-DD)
  whatsapp_number (always with country code, e.g. 919876543210)
  group_name
  city
  photo_file_name

🧠 Logic:
- If member.birthdate matches today (month & day) → send birthday image
- If member.anniversary matches today → send anniversary image
- Build caption text dynamically:
  - Birthday:  "Happy Birthday JSGian {name} ji 🎉\n{designation} – {group_name}, {city}\n\nWarm wishes from JSG."
  - Anniversary: "Happy Anniversary to {name} ji 💐\n{designation} – {group_name}, {city}\n\nWarm wishes from JSG."

🎨 Image Generation:
- Use Pillow library (PIL)
- Templates:
  templates/birthday_template.png
  templates/anniversary_template.png
- Coordinates to paste photo:
  PHOTO_POSITION = (80, 260)
  PHOTO_SIZE = (500, 500)
- Text placements (adjustable):
  NAME_POSITION = (650, 320)
  DESIGNATION_POSITION = (650, 410)
  GROUP_CITY_POSITION = (650, 490)
- Export to:
  output/birthday/<filename>.jpg
  output/anniversary/<filename>.jpg

📂 Project Structure:
jsg_wishes/
  .env
  google-service-account.json
  templates/
    birthday_template.png
    anniversary_template.png
  photos/
    <all member images from pdf extracted>
  output/
  sheets_client.py        # reads Google Sheets
  image_generator.py      # generates personalized image
  whatsapp_client.py      # uploads media & sends WhatsApp messages
  daily_wishes.py         # main script/cron execution
  requirements.txt

🔑 Config:
- Use python-dotenv to load .env with:
  GOOGLE_SHEET_ID=<sheet ID>
  WHATSAPP_TOKEN=<token>
  WHATSAPP_PHONE_NUMBER_ID=<phone number ID>
  WHATSAPP_SENDER=<full whatsapp phone number>
  WHATSAPP_API_VERSION=v21.0

🌍 Google Sheets:
- Use gspread + google-auth service account

📲 WhatsApp:
- Use WhatsApp Cloud API
- Upload generated image to /media to get media_id
- Then send message with caption using /messages endpoint
- Handle errors with try/except and print logs

📦 Requirements:
gspread
google-auth
python-dotenv
pillow
requests
python-dateutil

⏰ Automation:
- When running `python daily_wishes.py`:
  - Print how many birthdays and anniversaries found
  - Loop and send each message
- Later: Cron or Task Scheduler for daily run

✨ Future Enhancements (don’t build yet):
- Logging to Google Sheet
- PDF extraction for initial photos
- Retry mechanism for failed sends
- Multi-group support UI

📝 Important Notes:
- Code must be clean, modular, commented, production-ready
- Do not mix multiple major purposes in one file — separation of concerns is required
- No hard-coded credentials — everything must come from `.env` or Google Sheet
- Support flexibility for template updates later

➡️ Your job as Copilot:
- Generate and improve each file based on these specs
- Suggest refactoring and improvements
- Help me debug errors and maintain system reliability
