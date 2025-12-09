import os
import requests
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")

BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"

class WhatsAppClient:
    def __init__(self, token: Optional[str] = None, phone_number_id: Optional[str] = None):
        self.token = token or WHATSAPP_TOKEN
        self.phone_number_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID
        if not self.token or not self.phone_number_id:
            raise ValueError("WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID must be set in environment")
        self.headers = {
            "Authorization": f"Bearer {self.token}"
        }

    def upload_media(self, image_path: str) -> Optional[str]:
        """Upload an image to WhatsApp Cloud API /media endpoint and return media id on success."""
        url = f"{BASE_URL}/{self.phone_number_id}/media"
        files = {"file": open(image_path, "rb")}
        try:
            resp = requests.post(url, headers=self.headers, files=files)
            resp.raise_for_status()
            data = resp.json()
            return data.get("id")
        except Exception as e:
            print(f"Failed to upload media: {e} | response: {getattr(resp, 'text', None)}")
            return None
        finally:
            try:
                files['file'].close()
            except Exception:
                pass

    def send_image_message(self, to_whatsapp_number: str, media_id: str, caption: str) -> bool:
        """Send an image message with caption to a WhatsApp number using media_id."""
        url = f"{BASE_URL}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_whatsapp_number,
            "type": "image",
            "image": {
                "id": media_id,
                "caption": caption
            }
        }
        try:
            resp = requests.post(url, headers={**self.headers, "Content-Type": "application/json"}, json=payload)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send WhatsApp message to {to_whatsapp_number}: {e} | response: {getattr(resp, 'text', None)}")
            return False
