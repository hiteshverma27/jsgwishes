import os
from PIL import Image, ImageDraw, ImageFont
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "templates")
PHOTOS_DIR = os.getenv("PHOTOS_DIR", "photos")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
FONTS_DIR = os.getenv("FONTS_DIR", "fonts")

# Positions and sizes (from instructions)
PHOTO_POSITION = (80, 260)
PHOTO_SIZE = (500, 500)
NAME_POSITION = (650, 320)
DESIGNATION_POSITION = (650, 410)
GROUP_CITY_POSITION = (650, 490)

DEFAULT_BOLD = os.path.join(FONTS_DIR, "Montserrat-Bold.ttf")
DEFAULT_REGULAR = os.path.join(FONTS_DIR, "Montserrat-Regular.ttf")

class ImageGenerator:
    def __init__(self, templates_dir: str = None, photos_dir: str = None, output_dir: str = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.photos_dir = photos_dir or PHOTOS_DIR
        self.output_dir = output_dir or OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "birthday"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "anniversary"), exist_ok=True)

    def _load_font(self, path: str, size: int):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    def generate(self, member: Dict, kind: str = "birthday") -> str:
        """Generate an image for a member.

        member: dict with keys 'name', 'designation', 'group_name', 'city', 'photo_file_name', 'id'
        kind: 'birthday' or 'anniversary'

        Returns the path to the generated image.
        """
        assert kind in ("birthday", "anniversary")
        template_name = f"{kind}_template.png"
        template_path = os.path.join(self.templates_dir, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Load template
        base = Image.open(template_path).convert("RGBA")

        # Load photo
        photo_name = member.get("photo_file_name") or ""
        photo_path = os.path.join(self.photos_dir, photo_name)
        if not os.path.exists(photo_path):
            # create a placeholder solid color image
            photo = Image.new("RGB", PHOTO_SIZE, (200, 200, 200))
        else:
            photo = Image.open(photo_path).convert("RGB")
            photo = photo.resize(PHOTO_SIZE)

        # Paste photo
        base.paste(photo, PHOTO_POSITION)

        draw = ImageDraw.Draw(base)

        # Fonts
        name_font = self._load_font(DEFAULT_BOLD, 48)
        reg_font = self._load_font(DEFAULT_REGULAR, 34)

        # Text
        name = member.get("name", "")
        designation = member.get("designation", "")
        group = member.get("group_name", "")
        city = member.get("city", "")

        group_city = ", ".join([p for p in (group, city) if p])

        draw.text(NAME_POSITION, name, font=name_font, fill=(0, 0, 0))
        draw.text(DESIGNATION_POSITION, designation, font=reg_font, fill=(0, 0, 0))
        draw.text(GROUP_CITY_POSITION, group_city, font=reg_font, fill=(0, 0, 0))

        # Build output filename
        member_id = member.get("id") or member.get("whatsapp_number") or name.replace(" ", "_")
        fname = f"{member_id}_{kind}.jpg"
        out_dir = os.path.join(self.output_dir, kind)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, fname)

        # Convert to RGB and save as JPEG
        base.convert("RGB").save(out_path, "JPEG", quality=90)
        return out_path
