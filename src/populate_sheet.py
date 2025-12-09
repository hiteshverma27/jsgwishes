"""Read an extracted CSV and append rows to the configured Google Sheet.

This script expects a CSV with at minimum `photo_file_name` and `raw_text` columns.
You will usually run `src.text_extractor` first to generate the CSV.

Usage:
  python -m src.populate_sheet --csv output/extracted_text.csv --worksheet "JSG Members"

Behavior:
- Tries to parse each CSV row to fill fields: id, name, designation, birthdate, anniversary, whatsapp_number, group_name, city, photo_file_name
- Parsing is heuristic: dates (YYYY-MM-DD), phone numbers (10-13 digits) are extracted using regex.
- Rows that cannot be parsed into minimal required fields are still appended but may need manual cleanup in the sheet.
"""
import os
import csv
import re
import argparse
from typing import List
from src.sheets_client import SheetsClient

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
PHONE_RE = re.compile(r"(\d{10,13})")


def heuristics_from_text(text: str, photo_file_name: str) -> dict:
    # Attempt to pick out sensible fields from a block of text
    # Very heuristic: find first date occurrences and phone, and treat first non-empty line as name
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    name = lines[0] if lines else ''
    designation = lines[1] if len(lines) > 1 else ''
    group = ''
    city = ''
    birthdate = ''
    anniversary = ''
    phone = ''

    d_matches = DATE_RE.findall(text)
    if d_matches:
        # assign first to birthdate, second to anniversary if present
        birthdate = d_matches[0]
        if len(d_matches) > 1:
            anniversary = d_matches[1]

    p_match = PHONE_RE.search(text)
    if p_match:
        phone = p_match.group(1)

    return {
        'id': photo_file_name.replace(' ', '_'),
        'name': name,
        'designation': designation,
        'birthdate': birthdate,
        'anniversary': anniversary,
        'whatsapp_number': phone,
        'group_name': group,
        'city': city,
        'photo_file_name': photo_file_name,
    }


def main(csv_path: str, worksheet: str = 'JSG Members'):
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return

    rows_to_append: List[dict] = []
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            raw = r.get('raw_text', '')
            photo = r.get('photo_file_name') or ''
            if not photo and 'source_file' in r:
                photo = r.get('source_file')
            parsed = heuristics_from_text(raw, photo)
            rows_to_append.append(parsed)

    sheets = SheetsClient()
    print(f"Appending {len(rows_to_append)} rows to worksheet {worksheet}")
    sheets.append_rows(rows_to_append, worksheet_name=worksheet)
    print("Done")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Populate Google Sheet from extracted CSV')
    parser.add_argument('--csv', default='output/extracted_text.csv')
    parser.add_argument('--worksheet', default='JSG Members')
    args = parser.parse_args()
    main(args.csv, args.worksheet)
