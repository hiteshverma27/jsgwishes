"""Extract images from PDFs in an input directory into the photos directory.

Uses PyMuPDF (fitz). Example:

python -m src.pdf_extract_photos --input-dir input --output-dir photos

This is a helper script for populating `photos/` from PDF inputs.
"""
import os
import argparse
import fitz  # PyMuPDF


def extract_images_from_pdf(pdf_path: str, out_dir: str):
    doc = fitz.open(pdf_path)
    basename = os.path.splitext(os.path.basename(pdf_path))[0]
    count = 0
    for page_index in range(len(doc)):
        images = doc.get_page_images(page_index)
        for img_index, img in enumerate(images, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image.get("ext", "png")
            fname = f"{basename}_p{page_index+1}_{xref}.{ext}"
            out_path = os.path.join(out_dir, fname)
            with open(out_path, "wb") as f:
                f.write(image_bytes)
            count += 1
    return count


def main(input_dir: str, output_dir: str, recursive: bool = False):
    os.makedirs(output_dir, exist_ok=True)
    total = 0
    if recursive:
        for root, dirs, files in os.walk(input_dir):
            for f in files:
                if f.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, f)
                    print(f"Processing {pdf_path}")
                    total += extract_images_from_pdf(pdf_path, output_dir)
    else:
        for f in os.listdir(input_dir):
            if f.lower().endswith(".pdf"):
                pdf_path = os.path.join(input_dir, f)
                print(f"Processing {pdf_path}")
                total += extract_images_from_pdf(pdf_path, output_dir)

    print(f"Extracted {total} images to {output_dir}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract images from PDFs into an output folder")
    parser.add_argument("--input-dir", default="input", help="Input directory containing PDF files")
    parser.add_argument("--output-dir", default="photos", help="Output directory to save extracted images")
    parser.add_argument("--recursive", action="store_true", help="Recursively search input directory for PDFs")
    args = parser.parse_args()
    main(args.input_dir, args.output_dir, args.recursive)
