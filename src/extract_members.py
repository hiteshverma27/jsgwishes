#!/usr/bin/env python3
"""Extract member data from PDF forms using OCR (optimized version).

Writes results progressively to CSV as they're found.

Usage:
  python3 -m src.extract_members --input-dir input --output-csv output/members.csv
"""
import os
import csv
import re
import argparse
from typing import Dict
import fitz
import pytesseract
from PIL import Image
import io


def normalize_date(date_str: str) -> str:
    """Normalize date to YYYY-MM-DD."""
    if not date_str:
        return ""
    date_str = date_str.strip()
    match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', date_str)
    if match:
        try:
            d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return f"{y:04d}-{m:02d}-{d:02d}"
        except:
            pass
    return ""


def ocr_page_region(doc, page_num: int, rect) -> str:
    """Extract text from a page region using OCR."""
    try:
        pix = doc[page_num].get_pixmap(clip=rect, matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        img_data = pix.tobytes("ppm")
        img = Image.frombytes("RGB", [pix.width, pix.height], img_data)
        text = pytesseract.image_to_string(img, config='--psm 6')
        return text
    except:
        return ""


def parse_member_text(text: str, group_name: str) -> Dict:
    """Parse member info from OCR text."""
    member = {
        'id': '',
        'name': '',
        'designation': '',
        'birthdate': '',
        'anniversary': '',
        'whatsapp_number': '',
        'group_name': group_name,
        'city': '',
        'photo_file_name': '',
    }
    
    if not text.strip():
        return member
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # Extract name (first capitalized line without special keywords)
    for line in lines:
        if line and line[0].isupper():
            if not any(x.lower() in line.lower() for x in ['date', 'phone', 'mobile', 'address', 'city']):
                member['name'] = line[:60]  # Limit length
                break
    
    # Extract dates
    dates = re.findall(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
    if dates:
        member['birthdate'] = normalize_date(f"{dates[0][0]}/{dates[0][1]}/{dates[0][2]}")
        if len(dates) > 1:
            member['anniversary'] = normalize_date(f"{dates[1][0]}/{dates[1][1]}/{dates[1][2]}")
    
    # Extract phone numbers
    phones = re.findall(r'\b(\d{10,13})\b', text)
    if phones:
        # Prefer longer numbers
        member['whatsapp_number'] = sorted(set(phones), key=len, reverse=True)[0]
    
    # Extract designation
    for line in lines[1:4]:  # Check 2nd-4th lines
        if line and not any(x in line for x in ['/', '(', ')']):
            if len(line) < 100:
                member['designation'] = line
                break
    
    return member


def extract_group_name(filename: str) -> str:
    """Extract group from filename."""
    basename = os.path.splitext(filename)[0]
    match = re.match(r'^\d+\s*-\s*(.+)$', basename)
    return match.group(1).strip() if match else basename


def process_pdf(pdf_path: str, group_name: str) -> list:
    """Process one PDF and return list of members."""
    members = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_rect = page.rect
            
            # Define member form box regions (typical 2x3 layout per page)
            # Adjust these based on your PDF layout
            regions = []
            
            # Skip top 15% (header)
            top_margin = page_rect.height * 0.12
            
            # Create grid: 2 columns, 3 rows
            col_width = page_rect.width * 0.5
            row_height = (page_rect.height - top_margin) / 3
            
            for row in range(3):
                for col in range(2):
                    y0 = top_margin + (row * row_height)
                    y1 = y0 + row_height
                    if y1 > page_rect.height - 10:
                        continue
                    
                    x0 = col * col_width
                    x1 = x0 + col_width
                    
                    rect = fitz.Rect(x0, y0, x1, y1)
                    regions.append(rect)
            
            # OCR each region
            for rect in regions:
                text = ocr_page_region(doc, page_num, rect)
                if text.strip():
                    member = parse_member_text(text, group_name)
                    if member['name'] and member['whatsapp_number']:
                        members.append(member)
        
        doc.close()
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
    
    return members


def main(input_dir: str, output_csv: str):
    """Main extraction with progressive CSV writing."""
    os.makedirs(os.path.dirname(output_csv) or '.', exist_ok=True)
    
    pdf_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')])
    
    print(f"Found {len(pdf_files)} PDF files\n", flush=True)
    
    fieldnames = ['id', 'name', 'designation', 'birthdate', 'anniversary', 
                  'whatsapp_number', 'group_name', 'city', 'photo_file_name']
    
    total_members = 0
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, filename in enumerate(pdf_files, 1):
            pdf_path = os.path.join(input_dir, filename)
            group_name = extract_group_name(filename)
            
            print(f"[{idx:2d}/{len(pdf_files)}] {filename:55s}", end=" ", flush=True)
            
            members = process_pdf(pdf_path, group_name)
            
            # Write to CSV immediately
            for member in members:
                member['id'] = str(total_members + 1)
                writer.writerow({k: member.get(k, '') for k in fieldnames})
                total_members += 1
            
            csvfile.flush()  # Flush after each PDF
            
            print(f"✓ {len(members):3d}", flush=True)
    
    print(f"\n{'='*70}")
    print(f"Total members: {total_members}")
    print(f"Saved to: {output_csv}")
    print(f"{'='*70}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract members from PDF forms')
    parser.add_argument('--input-dir', default='input')
    parser.add_argument('--output-csv', default='output/members.csv')
    args = parser.parse_args()
    
    main(args.input_dir, args.output_csv)
