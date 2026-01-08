#!/usr/bin/env python3
"""Clean and validate the extracted members CSV.

Removes noise and low-quality entries, validates data formats.
"""
import csv
import re
from collections import defaultdict


def is_valid_member(row: dict) -> bool:
    """Check if a row represents a real member."""
    name = row.get('name', '').strip()
    phone = row.get('whatsapp_number', '').strip()
    
    # Must have both name and phone
    if not name or not phone or len(name) < 3 or len(phone) < 10:
        return False
    
    # Phone should be all digits
    if not phone.isdigit():
        return False
    
    # Filter out obvious noise patterns - must start with alphabetic character
    if not name[0].isalpha():
        return False
    
    # Filter out patterns that are clearly not names
    noise_keywords = [
        'address', 'city', 'phone', 'mobile', 'whatsapp', 'email', 'date', 
        'pin code', 'code', 'copy', 'federation', 'district', 'state', 'india',
        'size', 'bsp no', 'ship no', 'ncode', 'rajasthan', 'group copy',
        'region', 'zone', 'member', 'committee', 'general meeting'
    ]
    
    name_lower = name.lower()
    for keyword in noise_keywords:
        if keyword in name_lower:
            # Special case: if name is just the keyword, it's noise
            if len(name_lower) < len(keyword) * 2:
                return False
    
    # Name should look like person(s) name: multiple capitalized words
    # Pattern: "FirstName LastName" or "FirstName MiddleName LastName"
    # Allow for names with hyphens or apostrophes
    name_pattern = r'^([A-Z][a-z]+[\s\-\']?)+([A-Z][a-z]+)?'
    if not re.match(name_pattern, name):
        # If doesn't match pattern, require at least 15 chars and multiple words
        if len(name) < 15 or len(name.split()) < 2:
            return False
    
    return True


def clean_csv(input_file: str, output_file: str) -> int:
    """Clean the CSV and write validated members."""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Filter valid members
    valid_members = [r for r in rows if is_valid_member(r)]
    
    # Remove duplicates (same name and phone)
    seen = set()
    unique_members = []
    for member in valid_members:
        key = (member['name'].strip(), member['whatsapp_number'].strip())
        if key not in seen:
            seen.add(key)
            unique_members.append(member)
    
    # Write cleaned CSV
    if unique_members:
        fieldnames = ['id', 'name', 'designation', 'birthdate', 'anniversary', 
                      'whatsapp_number', 'group_name', 'city', 'photo_file_name']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for idx, member in enumerate(unique_members, 1):
                member['id'] = str(idx)
                writer.writerow({k: member.get(k, '') for k in fieldnames})
    
    return len(unique_members)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean extracted members CSV')
    parser.add_argument('--input', default='output/members.csv')
    parser.add_argument('--output', default='output/members_clean.csv')
    args = parser.parse_args()
    
    count = clean_csv(args.input, args.output)
    print(f"✓ Cleaned CSV: {count} valid members")
    print(f"✓ Saved to: {args.output}")
