#!/usr/bin/env python3
"""
Split a PDF into black-and-white and color PDFs based on page content.

Usage:
    python pdf_check.py input.pdf
    python pdf_check.py input.pdf -b bw.pdf -c color.pdf -t 15
"""

import sys
import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is required. Install with: pip install PyMuPDF")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


def page_has_color(page, threshold=10, zoom=1.5):
    """Check if a PDF page contains any color content by analyzing rendered pixels."""
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    # Downscale to thumbnail for faster analysis
    img.thumbnail((200, 200))

    for r, g, b in img.getdata():
        if max(r, g, b) - min(r, g, b) > threshold:
            return True
    return False


def split_pdf_by_color(input_pdf, bw_output, color_output, threshold=10, zoom=1.5, cutoff_page=None):
    """Split a PDF into B&W and color PDFs.

    Args:
        input_pdf: Path to input PDF file.
        bw_output: Path for output B&W PDF.
        color_output: Path for output color PDF.
        threshold: Color detection threshold (0-255).
        zoom: Render resolution multiplier.
        cutoff_page: If set, pages after this page number (1-based)
                     are treatd as B&W without color detection.
    Returns:
        dict with keys: bw_pages, color_pages, page_count, bw_count, color_count
    """
    doc = fitz.open(input_pdf)
    bw_indices = []
    color_indices = []
    total = doc.page_count

    print(f"Processing {total} pages...")

    for i in range(total):
        # If cutoff is set and page number (1-based) > cutoff, skip color check
        if cutoff_page is not None and (i + 1) > cutoff_page:
            bw_indices.append(i)
            label = "B&W (cutoff)"
        elif page_has_color(doc[i], threshold, zoom):
            color_indices.append(i)
            label = "COLOR"
        else:
            bw_indices.append(i)
            label = "B&W"
        print(f"  Page {i + 1}: {label}")

    def save_pdf(pages, output_path, label):
        if not pages:
            print(f"\nNo {label} pages found.")
            return
        out = fitz.open()
        out.insert_pdf(doc, from_page=pages[0], to_page=pages[0])
        for p in pages[1:]:
            out.insert_pdf(doc, from_page=p, to_page=p)
        out.save(output_path)
        out.close()
        print(f"\nSaved {len(pages)} {label} pages to: {output_path}")

    save_pdf(bw_indices, bw_output, "B&W")
    save_pdf(color_indices, color_output, "color")

    doc.close()

    return {
        "bw_pages": bw_indices,
        "color_pages": color_indices,
        "page_count": total,
        "bw_count": len(bw_indices),
        "color_count": len(color_indices),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Split a PDF into B&W and color PDFs based on page content."
    )
    parser.add_argument("input_pdf", help="Path to input PDF file")
    parser.add_argument(
        "-b", "--bw-output",
        help="Output path for B&W PDF (default: <input>_bw.pdf)"
    )
    parser.add_argument(
        "-c", "--color-output",
        help="Output path for color PDF (default: <input>_color.pdf)"
    )
    parser.add_argument(
        "-t", "--threshold",
        type=int,
        default=10,
        help="Color sensitivity 0-255 (default: 10). Lower = more sensitive."
    )
    parser.add_argument(
        "-z", "--zoom",
        type=float,
        default=1.5,
        help="Render zoom (default: 1.5). Higher = slower but more accurate."
    )
    parser.add_argument(
        "-n", "--cutoff",
        type=int,
        default=None,
        help="Pages after this number (1-based) are treated as B&W directly."
    )

    args = parser.parse_args()
    input_path = Path(args.input_pdf)

    if not input_path.exists():
        print(f"Error: file not found: {args.input_pdf}")
        sys.exit(1)

    stem = input_path.stem
    parent = input_path.parent
    bw_output = args.bw_output or str(parent / f"{stem}_bw.pdf")
    color_output = args.color_output or str(parent / f"{stem}_color.pdf")

    split_pdf_by_color(
        args.input_pdf, bw_output, color_output,
        threshold=args.threshold, zoom=args.zoom, cutoff_page=args.cutoff,
    )


if __name__ == "__main__":
    main()
