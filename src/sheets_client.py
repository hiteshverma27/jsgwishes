import os
from typing import List, Dict
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "google-service-account.json")

SCOPE = [
    # allow read + write so we can append rows later
    "https://www.googleapis.com/auth/spreadsheets",
]

class SheetsClient:
    """Small wrapper around gspread to fetch members from the configured Google Sheet.

    Methods:
    - get_members() -> List[Dict]

    Expects the sheet to have header row with columns matching the spec in instructions.md
    (id, name, designation, birthdate, anniversary, whatsapp_number, group_name, city, photo_file_name)
    """

    def __init__(self, sheet_id: str = None, service_account_file: str = None):
        self.sheet_id = sheet_id or GOOGLE_SHEET_ID
        self.service_account_file = service_account_file or SERVICE_ACCOUNT_FILE
        if not self.sheet_id:
            raise ValueError("GOOGLE_SHEET_ID must be set in environment or passed to SheetsClient")

        creds = Credentials.from_service_account_file(self.service_account_file, scopes=SCOPE)
        self.gc = gspread.authorize(creds)

    def get_members(self, worksheet_name: str = "JSG Members") -> List[Dict]:
        """Return list of member dicts (keys from header row).

        The function attempts to coerce blank cells to None.
        """
        sh = self.gc.open_by_key(self.sheet_id)
        try:
            ws = sh.worksheet(worksheet_name)
        except Exception:
            # fallback to first sheet
            ws = sh.get_worksheet(0)

        all_values = ws.get_all_records()  # returns list of dicts using header row
        # normalize keys to expected ones (strip)
        normalized = []
        for row in all_values:
            cleaned = {k.strip(): (v if v != "" else None) for k, v in row.items()}
            normalized.append(cleaned)
        return normalized

    def append_rows(self, rows: List[Dict], worksheet_name: str = "JSG Members") -> None:
        """Append multiple rows to the sheet. Expects rows as list of dicts where keys match header names.

        If the worksheet doesn't contain headers, this will write headers first.
        """
        sh = self.gc.open_by_key(self.sheet_id)
        try:
            ws = sh.worksheet(worksheet_name)
        except Exception:
            ws = sh.get_worksheet(0)

        # Get existing headers
        try:
            headers = ws.row_values(1)
        except Exception:
            headers = []

        # If no headers, create them from keys of first row
        if not headers and rows:
            headers = list(rows[0].keys())
            ws.append_row(headers)

        # Build rows in header order
        to_append = []
        for r in rows:
            row_values = [r.get(h, "") for h in headers]
            to_append.append(row_values)

        # gspread has append_rows
        if to_append:
            ws.append_rows(to_append, value_input_option='USER_ENTERED')
