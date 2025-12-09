"""Create simple placeholder templates for birthday and anniversary.

This script will create `templates/birthday_template.png` and `templates/anniversary_template.png`
if they don't already exist. Templates are simple colored backgrounds so you can run local tests.
"""
import os
from PIL import Image, ImageDraw, ImageFont

TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "templates")
WIDTH, HEIGHT = 1200, 800

os.makedirs(TEMPLATES_DIR, exist_ok=True)

def make_template(path, color, label):
    if os.path.exists(path):
        print(f"Template exists: {path}")
        return
    im = Image.new('RGB', (WIDTH, HEIGHT), color=color)
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype('arial.ttf', 40)
    except Exception:
        font = ImageFont.load_default()
    text = label
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except Exception:
        try:
            w, h = font.getsize(text)
        except Exception:
            w, h = (len(text) * 10, 20)
    draw.text(((WIDTH-w)/2, 50), text, fill=(255,255,255), font=font)
    im.save(path)
    print(f"Created template: {path}")

if __name__ == '__main__':
    make_template(os.path.join(TEMPLATES_DIR, 'birthday_template.png'), (255,165,0), 'Birthday Template')
    make_template(os.path.join(TEMPLATES_DIR, 'anniversary_template.png'), (70,130,180), 'Anniversary Template')
