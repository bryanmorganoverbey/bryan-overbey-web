#!/usr/bin/env python3
"""
Fuel Receipt Sorter with OCR Support
Sorts PDF pages of fuel receipts by vehicle name using OCR for problematic PDFs.
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Error: pypdf library not found. Please install it with:")
    print("  pip install pypdf")
    sys.exit(1)

try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: OCR libraries not available. Install with:")
    print("  pip install pdf2image pytesseract")
    print("  brew install tesseract poppler")


def is_text_garbled(text: str) -> bool:
    """
    Check if extracted text is garbled (custom font encoding issue).

    Args:
        text: Extracted text from PDF

    Returns:
        True if text appears garbled, False otherwise
    """
    # Check for patterns like /0/1/2 or /i255 which indicate encoding issues
    if re.search(r'/\d+|/i\d+', text):
        return True

    # Check if text has very few readable characters
    readable_chars = sum(1 for c in text if c.isalnum() or c.isspace())
    total_chars = len(text)

    if total_chars > 0 and readable_chars / total_chars < 0.5:
        return True

    return False


def extract_text_with_ocr(pdf_path: str, page_num: int) -> str:
    """
    Extract text from a PDF page using OCR.

    Args:
        pdf_path: Path to the PDF file
        page_num: Page number (0-indexed)

    Returns:
        Extracted text from the page
    """
    if not OCR_AVAILABLE:
        return ""

    try:
        # Convert single page to image
        images = convert_from_path(
            pdf_path,
            first_page=page_num + 1,
            last_page=page_num + 1,
            dpi=200
        )

        if images:
            # Perform OCR on the image
            text = pytesseract.image_to_string(images[0])
            return text
    except Exception as e:
        print(f"    OCR error: {e}")
        return ""

    return ""


def extract_vehicle_vin(page_text: str) -> tuple:
    """
    Extract vehicle VIN (last 4 digits) from a receipt page.

    Args:
        page_text: Text content of the PDF page

    Returns:
        Tuple of (vin_last_4, full_vehicle_name) or ("Unknown", "Unknown") if not found
    """
    lines = page_text.split('\n')

    # Method 1: Look for "Vehicle" label and extract from nearby lines
    for i, line in enumerate(lines):
        stripped_line = line.strip()

        # Check if this line contains "Vehicle" and "Fuel Type" together (OCR format)
        if 'Vehicle' in stripped_line and 'Fuel Type' in stripped_line:
            # The vehicle name should be on the PREVIOUS line
            if i > 0:
                prev_line = lines[i - 1].strip()
                # Look for vehicle name pattern: "Name #### diesel/gas"
                vehicle_match = re.search(r'(.+?)\s+(\d{4})\s+(?:diesel|gas|gasoline)', prev_line, re.IGNORECASE)
                if vehicle_match:
                    vehicle_name = f"{vehicle_match.group(1).strip()} {vehicle_match.group(2)}"
                    vin_last_4 = vehicle_match.group(2)
                    return (vin_last_4, vehicle_name)

        # Check if this line contains exactly "Vehicle" label (original format)
        if stripped_line == 'Vehicle':
            # The vehicle name should be on the PREVIOUS line
            if i > 0:
                vehicle_name = lines[i - 1].strip()
                # Make sure it's not empty and not another label
                if vehicle_name and vehicle_name not in ['', ' ']:
                    # Extract last 4 digits from the vehicle name
                    vin_last_4 = extract_last_4_digits(vehicle_name)
                    if vin_last_4 != "Unknown":
                        return (vin_last_4, vehicle_name)

    # Method 2: Look for vehicle name patterns anywhere in the text
    # Pattern: Vehicle name followed by 4 digits and fuel type
    vehicle_pattern = r'([A-Z][A-Za-z\s]+?)\s+(\d{4})\s+(?:diesel|gas|gasoline)'
    match = re.search(vehicle_pattern, page_text, re.IGNORECASE)
    if match:
        vehicle_name = f"{match.group(1).strip()} {match.group(2)}"
        vin_last_4 = match.group(2)
        return (vin_last_4, vehicle_name)

    # Method 3: Look for common vehicle naming patterns
    vehicle_patterns = [
        r'(?:Stealth|Bus|Apollo|Colt|Ford|Outlaw|Renegade|Bases\s+Loaded|Slow\s+Motion|Viper|Zeus)\s+\d{4}',
        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+\d{4}',  # Capitalized words followed by 4 digits
    ]

    for pattern in vehicle_patterns:
        match = re.search(pattern, page_text)
        if match:
            vehicle_name = match.group(0).strip()
            vin_last_4 = extract_last_4_digits(vehicle_name)
            if vin_last_4 != "Unknown":
                return (vin_last_4, vehicle_name)

    # Method 4: Look for VIN at bottom of receipt (common in some formats)
    # Pattern: "veniclelD" or "vehicleID" followed by 4 digits
    bottom_vin_patterns = [
        r'venicle[lI][dD]\s+[a-z]*\s*(\d{4})',  # OCR might read "vehicle" as "venicle"
        r'vehicle[lI][dD]\s+[a-z]*\s*(\d{4})',
        r'INVOICE[#H]\s+\d+\s*(\d{4})',  # Sometimes VIN appears after invoice number
    ]

    for pattern in bottom_vin_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            vin_last_4 = match.group(1)
            return (vin_last_4, f"Vehicle {vin_last_4}")

    return ("Unknown", "Unknown")


def extract_last_4_digits(vehicle_name: str) -> str:
    """
    Extract the last 4 digits from a vehicle name.

    Args:
        vehicle_name: Vehicle name string (e.g., "Apollo 5875", "6509", "Stealth 6509")

    Returns:
        Last 4 digits as a string, or "Unknown" if not found
    """
    # Find all sequences of digits in the vehicle name
    digits = re.findall(r'\d+', vehicle_name)

    if digits:
        # Get the last sequence of digits
        last_digits = digits[-1]

        # If it's exactly 4 digits, return it
        if len(last_digits) == 4:
            return last_digits

        # If it's longer than 4 digits, take the last 4
        if len(last_digits) > 4:
            return last_digits[-4:]

        # If it's shorter than 4 digits, pad with zeros on the left
        if len(last_digits) < 4:
            return last_digits.zfill(4)

    return "Unknown"


def sort_pdf_by_vehicle(input_pdf_path: str, output_pdf_path: str = None, use_ocr: bool = False) -> None:
    """
    Sort PDF pages by vehicle VIN (last 4 digits) and create a new sorted PDF.

    Args:
        input_pdf_path: Path to the input PDF file
        output_pdf_path: Path to the output PDF file (optional)
        use_ocr: Force use of OCR even if text extraction works
    """
    input_path = Path(input_pdf_path)

    if not input_path.exists():
        print(f"Error: Input file '{input_pdf_path}' not found.")
        sys.exit(1)

    if not input_path.suffix.lower() == '.pdf':
        print(f"Error: Input file must be a PDF file.")
        sys.exit(1)

    # Generate output filename if not provided
    if output_pdf_path is None:
        output_pdf_path = str(input_path.parent / f"{input_path.stem}_sorted.pdf")

    print(f"Reading PDF: {input_pdf_path}")

    try:
        reader = PdfReader(input_pdf_path)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        sys.exit(1)

    total_pages = len(reader.pages)
    print(f"Total pages: {total_pages}")

    # Check if we need OCR by testing the first page
    needs_ocr = use_ocr
    if not needs_ocr:
        try:
            first_page_text = reader.pages[0].extract_text()
            if is_text_garbled(first_page_text):
                print("\n⚠️  Detected custom font encoding - switching to OCR mode")
                needs_ocr = True
                if not OCR_AVAILABLE:
                    print("Error: OCR is required but libraries are not installed.")
                    print("Please install: pip install pdf2image pytesseract")
                    print("And: brew install tesseract poppler")
                    sys.exit(1)
        except Exception:
            needs_ocr = True

    # Extract VINs and group pages
    # Structure: {vin_last_4: [(page_num, full_vehicle_name), ...]}
    vin_pages: Dict[str, List[Tuple[int, str]]] = defaultdict(list)

    print("\nExtracting vehicle VINs from pages...")
    if needs_ocr:
        print("Using OCR (this may take a while)...")

    for page_num, page in enumerate(reader.pages):
        try:
            if needs_ocr:
                text = extract_text_with_ocr(input_pdf_path, page_num)
            else:
                text = page.extract_text()

            vin_last_4, vehicle_name = extract_vehicle_vin(text)
            vin_pages[vin_last_4].append((page_num, vehicle_name))

            # Show progress every 10 pages or for first 5 pages
            if page_num < 5 or (page_num + 1) % 10 == 0:
                print(f"  Page {page_num + 1}/{total_pages}: VIN {vin_last_4} ({vehicle_name})")
            elif (page_num + 1) % 50 == 0:
                print(f"  ... processed {page_num + 1}/{total_pages} pages")

        except Exception as e:
            print(f"  Page {page_num + 1}: Error extracting text - {e}")
            vin_pages["Unknown"].append((page_num, "Unknown"))

    # Sort by VIN (last 4 digits) numerically, with "Unknown" at the end
    def sort_key(vin):
        if vin == "Unknown":
            return (1, "9999")  # Put Unknown at the end
        else:
            return (0, vin)  # Sort other VINs numerically

    sorted_vins = sorted(vin_pages.keys(), key=sort_key)

    print(f"\nFound {len(sorted_vins)} unique VINs:")
    for vin in sorted_vins:
        page_count = len(vin_pages[vin])
        # Get unique vehicle names for this VIN
        vehicle_names = set(name for _, name in vin_pages[vin])
        vehicle_names_str = ", ".join(sorted(vehicle_names))
        print(f"  VIN {vin}: {page_count} page(s) ({vehicle_names_str})")

    # Create new PDF with sorted pages
    print(f"\nCreating sorted PDF: {output_pdf_path}")
    writer = PdfWriter()

    for vin in sorted_vins:
        # Sort pages within each VIN group by page number
        for page_num, _ in sorted(vin_pages[vin], key=lambda x: x[0]):
            writer.add_page(reader.pages[page_num])

    # Write the output PDF
    try:
        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)
        print(f"\n✓ Successfully created sorted PDF: {output_pdf_path}")
        print(f"  Total pages: {len(writer.pages)}")
    except Exception as e:
        print(f"\nError writing output PDF: {e}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Sort fuel receipt PDF pages by vehicle VIN (last 4 digits) with OCR support.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s receipts.pdf
  %(prog)s receipts.pdf -o sorted_receipts.pdf
  %(prog)s receipts.pdf --ocr
  %(prog)s /path/to/receipts.pdf --output /path/to/output.pdf

Note: Pages are sorted by the last 4 digits of the VIN found in the Vehicle field.
      OCR is automatically used if the PDF has custom font encoding.
        """
    )

    parser.add_argument(
        'input_pdf',
        help='Path to the input PDF file containing fuel receipts'
    )

    parser.add_argument(
        '-o', '--output',
        dest='output_pdf',
        help='Path to the output PDF file (default: input_sorted.pdf)'
    )

    parser.add_argument(
        '--ocr',
        action='store_true',
        help='Force use of OCR even if text extraction works'
    )

    args = parser.parse_args()

    sort_pdf_by_vehicle(args.input_pdf, args.output_pdf, args.ocr)


if __name__ == '__main__':
    main()
