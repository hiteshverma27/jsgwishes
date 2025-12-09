"""Local test harness: generate one birthday and one anniversary image from an existing photo.

Run:
    python src/local_test.py

It picks the first image in `photos/` and composes two output images.
"""
import os
import sys
from src.image_generator import ImageGenerator

PHOTOS_DIR = os.getenv("PHOTOS_DIR", "photos")

def pick_first_photo(photos_dir: str):
    if not os.path.isdir(photos_dir):
        print(f"Photos directory not found: {photos_dir}")
        return None
    for f in os.listdir(photos_dir):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            return f
    return None


def main():
    photo = pick_first_photo(PHOTOS_DIR)
    if not photo:
        print("No photo files found in photos/. Run pdf extraction first or add photos.")
        sys.exit(1)

    member = {
        'id': 'testuser1',
        'name': 'Test User',
        'designation': 'Community Lead',
        'group_name': 'Test Group',
        'city': 'Test City',
        'photo_file_name': photo,
    }

    gen = ImageGenerator()
    print(f"Using photo: {photo}")
    out_b = gen.generate(member, kind='birthday')
    out_a = gen.generate(member, kind='anniversary')
    print(f"Generated birthday image: {out_b}")
    print(f"Generated anniversary image: {out_a}")

if __name__ == '__main__':
    main()
