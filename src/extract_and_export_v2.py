"""Extract member data from form-based PDFs and export to CSV.

This script handles structured PDF forms with fields like:
- Name
- Birth Date (DD/MM/YYYY format)
- WhatsApp No
- Marriage Date (Anniversary)
- Designation/Occupation
- Phone/Mobile
- Email
- Address/City
- Photo (embedded in form)

It uses OCR to extract text from form images and intelligently parses the structured fields.

Usage:
  python -m src.extract_and_export_v2 --input-dir input --output-csv output/members.csv --output-dir photos

The output CSV will have columns:
  id, name, designation, birthdate, anniversary, whatsapp_number, group_name, city, photo_file_name
"""
import os
import csv
import re
import argparse
from typing import List, Dict, Tuple
import fitz  # PyMuPDF

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def extract_images_from_pdf(pdf_path: str, out_dir: str, pdf_name: str) -> List[Tuple[int, str]]:
    """Extract images from a PDF file. Returns list of (page_number, filename) tuples."""
    try:
        doc = fitz.open(pdf_path)
        extracted_files = []
        for page_index in range(len(doc)):
            try:
                images = doc.get_page_images(page_index)
                for img_index, img in enumerate(images, start=1):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        ext = base_image.get("ext", "png")
                        fname = f"{pdf_name}_p{page_index+1}_{xref}.{ext}"
                        out_path = os.path.join(out_dir, fname)
                        with open(out_path, "wb") as f:
                            f.write(image_bytes)
                        extracted_files.append((page_index, fname))
                    except Exception as e:
                        print(f"    Warning: Failed to extract image {img_index} from page {page_index+1}: {e}")
            except Exception as e:
                print(f"    Warning: Failed to process page {page_index+1}: {e}")
        return extracted_files
    except Exception as e:
        print(f"  Error opening PDF {pdf_path}: {e}")
        return []


def render_pdf_page_to_image(pdf_path: str, page_index: int, zoom: float = 2.0):
    """Render a PDF page to PIL Image for OCR. zoom=2.0 for better OCR accuracy."""
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_index]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(img_data))
        return img
    except Exception as e:
        print(f"    Error rendering page {page_index+1}: {e}")
        return None


def extract_text_from_page_image(img) -> str:
    """Extract text from a PIL Image using OCR."""
    if not img or not OCR_AVAILABLE:
        return ""
    try:
        # Improve OCR accuracy with preprocessing
        text = pytesseract.image_to_string(img, config='--psm 6')
        return text.strip()
    except Exception as e:
        print(f"    Warning: OCR failed: {e}")
        return ""


def parse_form_fields(text: str) -> Dict[str, str]:
    """Parse structured form fields from OCR text.
    
    Expected fields:
    - Name:
    - Birth Date: DD/MM/YYYY
    - WhatsApp No: digits
    - Marriage Date: DD/MM/YYYY (Anniversary)
    - Occupation/Designation:
    - Mobile:
    - City/Address:
    - Email:
    """
    fields = {
        'name': '',
        'designation': '',
        'birthdate': '',
        'anniversary': '',
        'whatsapp_number': '',
        'city': '',
        'email': '',
        'phone': '',
    }
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        line_clean = line.strip()
        
        # Name - usually at the beginning, after "Name" label
        if re.match(r'^\s*name\s*[:=]?\s*$', line_lower, re.IGNORECASE) and i + 1 < len(lines):
            fields['name'] = lines[i + 1].strip()
        elif re.match(r'^name', line_lower, re.IGNORECASE) and ':' in line:
            name_part = re.split(r'[:=]', line, 1)[1].strip()
            if name_part:
                fields['name'] = name_part
        
        # Birth Date - DD/MM/YYYY or DD-MM-YYYY format
        if 'birth' in line_lower:
            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', line)
            if date_match:
                day, month, year = date_match.groups()
                fields['birthdate'] = f"{year}-{month:0>2}-{day:0>2}"
        
        # WhatsApp/Mobile number - 10+ digits
        if any(x in line_lower for x in ['whatsapp', 'mobile', 'phone']):
            phone_match = re.search(r'(\d{10,13})', line)
            if phone_match:
                phone = phone_match.group(1)
                if 'whatsapp' in line_lower:
                    fields['whatsapp_number'] = phone
                elif 'mobile' in line_lower:
                    fields['phone'] = phone
                elif 'phone' in line_lower and not fields['phone']:
                    fields['phone'] = phone
        
        # Marriage/Anniversary Date
        if 'marriage' in line_lower or 'anniversary' in line_lower or "spouse's birth" in line_lower.lower():
            # Try to find date in this line or next few lines
            for j in range(i, min(i + 3, len(lines))):
                date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', lines[j])
                if date_match and 'marriage' in line_lower:
                    day, month, year = date_match.groups()
                    fields['anniversary'] = f"{year}-{month:0>2}-{day:0>2}"
                    break
        
        # Occupation/Designation
        if re.match(r'.*occupation', line_lower, re.IGNORECASE) or re.match(r'.*designation', line_lower):
            occ_part = re.split(r'[:=]', line, 1)
            if len(occ_part) > 1:
                fields['designation'] = occ_part[1].strip()
            elif i + 1 < len(lines):
                fields['designation'] = lines[i + 1].strip()
        
        # City/Address
        if 'city' in line_lower or 'address' in line_lower:
            city_part = re.split(r'[:=]', line, 1)
            if len(city_part) > 1:
                fields['city'] = city_part[1].strip()
            elif i + 1 < len(lines):
                fields['city'] = lines[i + 1].strip()
        
        # Email
        if 'email' in line_lower or '@' in line:
            email_match = re.search(r'[\w.-]+@[\w.-]+', line)
            if email_match:
                fields['email'] = email_match.group(0)
    
    return fields


def extract_group_name_from_filename(filename: str) -> str:
    """Extract group name from PDF filename.
    
    Example: '084 - JSG CHITTORGARH.pdf' -> 'JSG CHITTORGARH'
    """
    basename = os.path.splitext(filename)[0]
    match = re.match(r'^\d+\s*-\s*(.+)$', basename)
    if match:
        return match.group(1).strip()
    return basename


def main(input_dir: str, output_csv: str, output_dir: str, recursive: bool = False):
    """Main extraction and export function."""
    if not OCR_AVAILABLE:
        print("ERROR: pytesseract and PIL are required but not available.")
        print("Please install: pip install pytesseract pillow")
        print("Also install Tesseract OCR from: https://github.com/tesseract-ocr/tesseract")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_csv) or '.', exist_ok=True)
    
    all_members = []
    pdf_files = []
    
    # Collect all PDF files
    if recursive:
        for root, dirs, files in os.walk(input_dir):
            for f in files:
                if f.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, f))
    else:
        for f in os.listdir(input_dir):
            if f.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(input_dir, f))
    
    print(f"Found {len(pdf_files)} PDF files\n")
    
    # Process each PDF
    for pdf_path in sorted(pdf_files):
        filename = os.path.basename(pdf_path)
        pdf_name = os.path.splitext(filename)[0]
        group_name = extract_group_name_from_filename(filename)
        
        print(f"Processing: {filename}")
        print(f"  Group: {group_name}")
        
        # Extract images for photo references
        print(f"  Extracting images...")
        extracted_photos = extract_images_from_pdf(pdf_path, output_dir, pdf_name)
        print(f"    Extracted {len(extracted_photos)} images")
        
        # Extract text from each page using OCR
        print(f"  Extracting text with OCR...")
        try:
            doc = fitz.open(pdf_path)
            num_pages = len(doc)
            
            for page_idx in range(num_pages):
                # Render page to image for better OCR
                img = render_pdf_page_to_image(pdf_path, page_idx, zoom=2.0)
                if not img:
                    continue
                
                text = extract_text_from_page_image(img)
                if not text:
                    continue
                
                # Parse form fields from the text
                fields = parse_form_fields(text)
                
                # Find photo for this page if available
                photo_file = ""
                for page_num, fname in extracted_photos:
                    if page_num == page_idx:
                        photo_file = fname
                        break
                
                # Create member entry if we have at least a name
                if fields['name']:
                    member = {
                        'id': f"{pdf_name}_{page_idx+1}",
                        'name': fields['name'],
                        'designation': fields['designation'],
                        'birthdate': fields['birthdate'],
                        'anniversary': fields['anniversary'],
                        'whatsapp_number': fields['whatsapp_number'],
                        'group_name': group_name,
                        'city': fields['city'],
                        'photo_file_name': photo_file,
                    }
                    all_members.append(member)
                    print(f"    Page {page_idx+1}: Extracted '{fields['name']}'")
        
        except Exception as e:
            print(f"  Error processing PDF: {e}")
    
    print(f"\n{'='*70}")
    print(f"Total members extracted: {len(all_members)}")
    print(f"Writing to CSV: {output_csv}")
    print(f"{'='*70}\n")
    
    # Write to CSV
    if all_members:
        fieldnames = ['id', 'name', 'designation', 'birthdate', 'anniversary', 
                      'whatsapp_number', 'group_name', 'city', 'photo_file_name']
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for member in all_members:
                writer.writerow({k: member.get(k, '') for k in fieldnames})
        
        print(f"✓ CSV file created: {output_csv}")
        print(f"✓ Photos extracted to: {output_dir}")
        print(f"\nFirst 10 entries:")
        print("-" * 70)
        for i, member in enumerate(all_members[:10], 1):
            print(f"{i}. {member['name']}")
            print(f"   Designation: {member['designation']}")
            print(f"   Birth Date: {member['birthdate']}")
            print(f"   Anniversary: {member['anniversary']}")
            print(f"   WhatsApp: {member['whatsapp_number']}")
            print(f"   Group: {member['group_name']}")
            print(f"   City: {member['city']}")
            if member['photo_file_name']:
                print(f"   Photo: {member['photo_file_name']}")
            print()
    else:
        print("No members found in PDFs")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract member data from form-based PDFs using OCR and export to CSV'
    )
    parser.add_argument('--input-dir', default='input', 
                        help='Input directory containing PDF files')
    parser.add_argument('--output-csv', default='output/members.csv',
                        help='Output CSV file path')
    parser.add_argument('--output-dir', default='photos',
                        help='Output directory for extracted images')
    parser.add_argument('--recursive', action='store_true',
                        help='Recursively search input directory for PDFs')
    args = parser.parse_args()
    
    main(args.input_dir, args.output_csv, args.output_dir, args.recursive)
