"""
Convert PDF pages to JPG files, OCR each page, and combine all text into one file.
Usage: python pdf_to_jpg_and_ocr.py [--ocr-only]
  --ocr-only  Use existing JPGs in the same folder; skip PDF conversion.
"""
import os
import sys

# Avoid UnicodeEncodeError on Windows when EasyOCR prints progress (e.g. block char U+2588)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# PDF path (same folder as this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SCRIPT_DIR, "sri-ramanavami-pooja-vidhanam.pdf")
OUTPUT_TEXT_PATH = os.path.join(SCRIPT_DIR, "sri-ramanavami-pooja-vidhanam-ocr.txt")
BASE_NAME = "sri-ramanavami-pooja-vidhanam"


def main():
    ocr_only = "--ocr-only" in sys.argv
    if not ocr_only and not os.path.isfile(PDF_PATH):
        print(f"PDF not found: {PDF_PATH}")
        sys.exit(1)

    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Installing PyMuPDF...")
        os.system(f'"{sys.executable}" -m pip install PyMuPDF')
        import fitz

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        print("Installing pytesseract and Pillow...")
        os.system(f'"{sys.executable}" -m pip install pytesseract Pillow')
        import pytesseract
        from PIL import Image

    # On Windows, try common Tesseract install locations if not in PATH
    use_easyocr = False
    if sys.platform == "win32":
        for path in (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LocalAppData%\Tesseract-OCR\tesseract.exe"),
        ):
            if os.path.isfile(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
        else:
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                use_easyocr = True
                print("Tesseract not found. Using EasyOCR (pip install easyocr) instead.")
    else:
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            use_easyocr = True
            print("Tesseract not found. Using EasyOCR instead.")

    if use_easyocr:
        try:
            import easyocr
        except ImportError:
            print("Installing EasyOCR (no Tesseract required)...")
            os.system(f'"{sys.executable}" -m pip install easyocr')
            import easyocr
        print("Loading EasyOCR model (first run may download models)...")
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)

    def ocr_image(img_or_path):
        if use_easyocr:
            texts = reader.readtext(img_or_path, detail=0)
            return "\n".join(texts) if texts else ""
        return pytesseract.image_to_string(Image.open(img_or_path) if isinstance(img_or_path, str) else img_or_path)

    jpg_dir = SCRIPT_DIR
    jpg_paths = []

    if ocr_only:
        # Use existing JPGs
        i = 1
        while True:
            p = os.path.join(jpg_dir, f"{BASE_NAME}_page_{i:03d}.jpg")
            if not os.path.isfile(p):
                break
            jpg_paths.append(p)
            i += 1
        if not jpg_paths:
            print("No existing JPGs found. Run without --ocr-only first.")
            sys.exit(1)
        print(f"Using {len(jpg_paths)} existing JPG(s).")
    else:
        base_name = os.path.splitext(os.path.basename(PDF_PATH))[0]
        dpi = 200
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        print(f"Opening PDF: {PDF_PATH}")
        doc = fitz.open(PDF_PATH)
        total_pages = len(doc)
        print(f"Pages: {total_pages}")
        for i in range(total_pages):
            page = doc[i]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            jpg_path = os.path.join(jpg_dir, f"{base_name}_page_{i + 1:03d}.jpg")
            pix.pil_save(jpg_path, format="JPEG", quality=90)
            jpg_paths.append(jpg_path)
            print(f"  Saved: {os.path.basename(jpg_path)}")
        doc.close()

    print("Running OCR on each page...")
    all_text_parts = []
    for i, jpg_path in enumerate(jpg_paths):
        text = ocr_image(jpg_path)
        all_text_parts.append(f"--- Page {i + 1} ---\n\n{text}")
        print(f"  OCR done: page {i + 1}")

    full_text = "\n\n".join(all_text_parts)
    with open(OUTPUT_TEXT_PATH, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"\nCombined text saved to: {OUTPUT_TEXT_PATH}")


if __name__ == "__main__":
    main()
