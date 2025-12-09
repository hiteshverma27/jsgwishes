import os
import argparse
from datetime import datetime
from dateutil import parser as date_parser
from dotenv import load_dotenv

from src.sheets_client import SheetsClient
from src.image_generator import ImageGenerator
from src.whatsapp_client import WhatsAppClient

load_dotenv()


def is_same_month_day(date_str: str, today: datetime) -> bool:
    if not date_str:
        return False
    try:
        dt = date_parser.parse(date_str)
        return (dt.month, dt.day) == (today.month, today.day)
    except Exception:
        return False


def build_caption(member: dict, kind: str) -> str:
    name = member.get("name", "")
    designation = member.get("designation", "")
    group = member.get("group_name", "")
    city = member.get("city", "")

    if kind == "birthday":
        return f"Happy Birthday JSGian {name} ji 🎉\n{designation} – {group}, {city}\n\nWarm wishes from JSG."
    else:
        return f"Happy Anniversary to {name} ji 💐\n{designation} – {group}, {city}\n\nWarm wishes from JSG."


def main(dry_run: bool = False):
    today = datetime.today()
    sheets = SheetsClient()
    members = sheets.get_members()

    image_gen = ImageGenerator()

    whatsapp = None
    if not dry_run:
        whatsapp = WhatsAppClient()

    birthdays = []
    anniversaries = []

    for m in members:
        try:
            if is_same_month_day(m.get("birthdate"), today):
                birthdays.append(m)
            if is_same_month_day(m.get("anniversary"), today):
                anniversaries.append(m)
        except Exception as e:
            print(f"Skipping row due to parse error: {e}")

    print(f"Found {len(birthdays)} birthdays and {len(anniversaries)} anniversaries for {today.date()}")

    # process birthdays
    for m in birthdays:
        try:
            out = image_gen.generate(m, kind="birthday")
            caption = build_caption(m, "birthday")
            print(f"Generated image: {out}")
            if dry_run:
                print(f"Dry-run: would send to {m.get('whatsapp_number')} with caption:\n{caption}")
            else:
                media_id = whatsapp.upload_media(out)
                if media_id:
                    sent = whatsapp.send_image_message(m.get("whatsapp_number"), media_id, caption)
                    print(f"Sent to {m.get('whatsapp_number')}: {sent}")
        except Exception as e:
            print(f"Error processing birthday for {m.get('name')}: {e}")

    # process anniversaries
    for m in anniversaries:
        try:
            out = image_gen.generate(m, kind="anniversary")
            caption = build_caption(m, "anniversary")
            print(f"Generated image: {out}")
            if dry_run:
                print(f"Dry-run: would send to {m.get('whatsapp_number')} with caption:\n{caption}")
            else:
                media_id = whatsapp.upload_media(out)
                if media_id:
                    sent = whatsapp.send_image_message(m.get("whatsapp_number"), media_id, caption)
                    print(f"Sent to {m.get('whatsapp_number')}: {sent}")
        except Exception as e:
            print(f"Error processing anniversary for {m.get('name')}: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Send daily wishes via WhatsApp Cloud API")
    parser.add_argument("--dry-run", action="store_true", help="Do everything except send messages")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
