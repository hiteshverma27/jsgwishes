"""Extract text from PDFs and images.

Usage:
  python -m src.text_extractor --input-dir input --out-csv output/extracted_text.csv

Behavior:
- For PDFs: attempts to extract selectable text via PyMuPDF (fast, accurate when PDF contains text).
- For images (jpg/png) or PDF pages without selectable text: optionally use pytesseract if available.
- Writes a CSV with columns: source_file, page, photo_file_name (for images), raw_text

Notes:
- OCR requires Tesseract binary installed on your system for pytesseract to work.
  - Windows: install Tesseract and add to PATH (https://github.com/tesseract-ocr/tesseract)
  - Linux: apt install tesseract-ocr
- This script produces raw text output; automated parsing into structured columns is heuristic and may require manual review.
"""
import os
import csv
import argparse
from typing import List
import fitz

try:
    import pytesseract
    from PIL import Image
    import cv2
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def extract_text_from_pdf(pdf_path: str) -> List[dict]:
    doc = fitz.open(pdf_path)
    results = []
    for i in range(len(doc)):
        # try to get selectable text
        text = doc.get_page_text(i)
        if text and text.strip():
            results.append({
                'source_file': os.path.basename(pdf_path),
                'page': i+1,
                'photo_file_name': '',
                'raw_text': text.strip()
            })
        else:
            # fallback to rendering page to image and OCR if available
            if OCR_AVAILABLE:
                pix = doc.load_page(i).get_pixmap(dpi=200)
                img_data = pix.tobytes()
                # write to temp and run OCR
                import tempfile
                ext = 'png'
                with tempfile.NamedTemporaryFile(suffix='.'+ext, delete=False) as tmp:
                    tmp.write(img_data)
                    tmp_path = tmp.name
                try:
                    ocr_text = pytesseract.image_to_string(Image.open(tmp_path))
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                results.append({
                    'source_file': os.path.basename(pdf_path),
                    'page': i+1,
                    'photo_file_name': '',
                    'raw_text': ocr_text.strip()
                })
            else:
                results.append({
                    'source_file': os.path.basename(pdf_path),
                    'page': i+1,
                    'photo_file_name': '',
                    'raw_text': ''
                })
    return results


def extract_text_from_image(image_path: str) -> dict:
    if not OCR_AVAILABLE:
        return {'source_file': os.path.basename(image_path), 'page': 0, 'photo_file_name': os.path.basename(image_path), 'raw_text': ''}
    # use OpenCV to load and possibly preprocess
    img = Image.open(image_path)
    # optional preprocessing: convert to grayscale
    try:
        gray = img.convert('L')
        text = pytesseract.image_to_string(gray)
    except Exception:
        text = pytesseract.image_to_string(img)
    return {'source_file': os.path.basename(image_path), 'page': 0, 'photo_file_name': os.path.basename(image_path), 'raw_text': text.strip()}


def main(input_dir: str, out_csv: str, recursive: bool = False):
    os.makedirs(os.path.dirname(out_csv) or '.', exist_ok=True)
    entries = []
    if recursive:
        for root, dirs, files in os.walk(input_dir):
            for f in files:
                path = os.path.join(root, f)
                if f.lower().endswith('.pdf'):
                    entries.extend(extract_text_from_pdf(path))
                elif f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    entries.append(extract_text_from_image(path))
    else:
        for f in os.listdir(input_dir):
            path = os.path.join(input_dir, f)
            if f.lower().endswith('.pdf'):
                entries.extend(extract_text_from_pdf(path))
            elif f.lower().endswith(('.png', '.jpg', '.jpeg')):
                entries.append(extract_text_from_image(path))

    # write CSV
    with open(out_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['source_file', 'page', 'photo_file_name', 'raw_text'])
        writer.writeheader()
        for e in entries:
            writer.writerow(e)

    print(f"Wrote {len(entries)} extracted-text rows to {out_csv}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract text from PDFs and images')
    parser.add_argument('--input-dir', default='input', help='Input directory containing PDFs/images')
    parser.add_argument('--out-csv', default='output/extracted_text.csv', help='CSV path to write extracted text')
    parser.add_argument('--recursive', action='store_true', help='Recursively search input dir')
    args = parser.parse_args()
    main(args.input_dir, args.out_csv, args.recursive)
