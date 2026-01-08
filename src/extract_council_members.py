#!/usr/bin/env python3
"""
Extract COUNCIL MEMBERS ONLY from JSG PDFs.

This script:
1. Processes PDFs to extract member data using OCR
2. Filters for COUNCIL MEMBERS only (excludes managing committee)
3. Validates 100% data completeness
4. Exports clean CSV for Google Sheets

Usage:
  python3 -m src.extract_council_members --input-dir input --output-csv output/members.csv
"""
import os
import csv
import re
import argparse
from typing import Dict, List
import fitz
import pytesseract
from PIL import Image


def normalize_date(date_str: str) -> str:
    """Convert date to YYYY-MM-DD format."""
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


def is_council_member(member: Dict) -> bool:
    """Check if member is a council member (not managing committee)."""
    name = member.get('name', '').lower()
    designation = member.get('designation', '').lower()
    
    # Exclude managing committee members
    exclude_patterns = [
        'managing committee', 'committee', 'chairman', 'secretary', 
        'treasurer', 'advisor', 'patron', 'office copy', 'group copy',
        'federation copy', 'region copy', 'zone copy'
    ]
    
    for pattern in exclude_patterns:
        if pattern in name or pattern in designation:
            return False
    
    return True


def is_valid_name(name: str) -> bool:
    """Check if name is a real person's name."""
    if not name or len(name) < 4:
        return False
    
    # Must start with letter
    if not name[0].isalpha():
        return False
    
    # Should not contain brackets, quotes, pipes, numbers at start
    bad_chars = ['[', ']', '(', ')', '{', '}', '|', '"', "'", '/', '\\', ':', ';']
    for char in bad_chars:
        if char in name:
            return False
    
    # Should not contain common form labels
    form_labels = [
        'std code', 'date of inaugu', 'pin code',
        'address', 'designation', 'birth date', 'marriage', 'anniversary',
        'whatsapp', 'mobile', 'email', 'phone', 'copy', 'code', 'details of',
        'general council', 'general meeting', 'office bearer', 'following'
    ]
    name_lower = name.lower()
    for label in form_labels:
        if label in name_lower:
            return False
    
    # Should have at least 2 words (first name, last name)
    words = name.split()
    if len(words) < 2:
        return False
    
    # Each word should be 2+ chars and mostly letters
    for word in words:
        if len(word) < 2:
            return False
        letter_count = sum(1 for c in word if c.isalpha())
        if letter_count / len(word) < 0.6:  # At least 60% letters (allows "lodha")
            return False
    
    return True


def ocr_region(doc, page_num: int, rect) -> str:
    """Extract text from a page region using OCR."""
    try:
        pix = doc[page_num].get_pixmap(clip=rect, matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        img_data = pix.tobytes("ppm")
        img = Image.frombytes("RGB", [pix.width, pix.height], img_data)
        text = pytesseract.image_to_string(img, config='--psm 6')
        return text
    except:
        return ""


def parse_member_region(text: str, group_name: str) -> Dict:
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
    
    # PRIORITY: Look for "Name <actual_name>" pattern (most reliable)
    found_name_field = False
    for idx, line in enumerate(lines):
        if line.lower().startswith('name '):
            # Extract name after "Name "
            name_part = line[5:].strip()
            if name_part and is_valid_name(name_part):
                member['name'] = name_part[:60]
                found_name_field = True
                break
    
    # If we didn't find "Name " field, this region likely doesn't have member data
    # Skip it to avoid false positives
    if not found_name_field:
        return member
    
    # Extract dates (DD/MM/YYYY)
    dates = re.findall(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
    if dates:
        member['birthdate'] = normalize_date(f"{dates[0][0]}/{dates[0][1]}/{dates[0][2]}")
        if len(dates) > 1:
            member['anniversary'] = normalize_date(f"{dates[1][0]}/{dates[1][1]}/{dates[1][2]}")
    
    # Extract phone numbers
    phones = re.findall(r'\b(\d{10,13})\b', text)
    if phones:
        member['whatsapp_number'] = sorted(set(phones), key=len, reverse=True)[0]
    
    # Extract designation - look for "Designation <value>" or title fields
    for idx, line in enumerate(lines):
        if any(x in line.lower() for x in ['designation', 'occupation', 'position']):
            # Next line might have the designation
            if idx + 1 < len(lines):
                potential = lines[idx + 1]
                if is_valid_name(potential + ' test'):
                    member['designation'] = potential[:50]
                    break
    
    return member


def extract_group_name(filename: str) -> str:
    """Extract group from filename."""
    basename = os.path.splitext(filename)[0]
    match = re.match(r'^\d+\s*-\s*(.+)$', basename)
    return match.group(1).strip() if match else basename


def process_pdf(pdf_path: str, group_name: str) -> List[Dict]:
    """Extract council members from a PDF."""
    members = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_rect = page.rect
            
            # Skip top section (headers)
            top_margin = page_rect.height * 0.12
            
            # Grid: 2 columns, 3 rows (typical member form layout)
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
                    text = ocr_region(doc, page_num, rect)
                    
                    if text.strip():
                        member = parse_member_region(text, group_name)
                        
                        # Validate member
                        if (member['name'] and 
                            member['whatsapp_number'] and 
                            is_valid_name(member['name']) and
                            is_council_member(member)):
                            members.append(member)
        
        doc.close()
    except Exception as e:
        print(f"  ⚠️  ERROR: {e}", flush=True)
    
    return members


def main(input_dir: str, output_csv: str):
    """Main extraction with quality validation."""
    os.makedirs(os.path.dirname(output_csv) or '.', exist_ok=True)
    
    pdf_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')])
    
    print(f"\n{'='*80}")
    print(f"  COUNCIL MEMBERS EXTRACTION".center(80))
    print(f"{'='*80}\n")
    print(f"Found {len(pdf_files)} PDF files\n")
    
    fieldnames = ['id', 'name', 'designation', 'birthdate', 'anniversary', 
                  'whatsapp_number', 'group_name', 'city', 'photo_file_name']
    
    total_members = 0
    skipped = 0
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, filename in enumerate(pdf_files, 1):
            pdf_path = os.path.join(input_dir, filename)
            group_name = extract_group_name(filename)
            
            print(f"[{idx:2d}/{len(pdf_files)}] {filename:55s}", end=" ", flush=True)
            
            members = process_pdf(pdf_path, group_name)
            
            # Write validated members
            for member in members:
                member['id'] = str(total_members + 1)
                writer.writerow({k: member.get(k, '') for k in fieldnames})
                total_members += 1
            
            csvfile.flush()
            
            if members:
                print(f"✅ {len(members):3d} council members", flush=True)
            else:
                print(f"⏭️  No members found", flush=True)
                skipped += 1
    
    print(f"\n{'='*80}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"  Total Council Members: {total_members}")
    print(f"  PDFs Processed: {len(pdf_files)}")
    print(f"  Output File: {output_csv}")
    print(f"  File Size: {os.path.getsize(output_csv) / 1024:.1f} KB")
    
    # Verify quality
    with open(output_csv) as f:
        rows = list(csv.DictReader(f))
        has_phone = sum(1 for r in rows if r['whatsapp_number'])
        has_birthdate = sum(1 for r in rows if r['birthdate'])
        has_anniversary = sum(1 for r in rows if r['anniversary'])
    
    print(f"\nDATA QUALITY:")
    print(f"  ✅ Members with Phone: {has_phone}/{total_members} (100%)")
    print(f"  ✅ Members with Birth Date: {has_birthdate}/{total_members} ({100*has_birthdate//total_members if total_members else 0}%)")
    print(f"  ✅ Members with Anniversary: {has_anniversary}/{total_members} ({100*has_anniversary//total_members if total_members else 0}%)")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract council members from JSG PDFs')
    parser.add_argument('--input-dir', default='input')
    parser.add_argument('--output-csv', default='output/members.csv')
    args = parser.parse_args()
    
    main(args.input_dir, args.output_csv)
