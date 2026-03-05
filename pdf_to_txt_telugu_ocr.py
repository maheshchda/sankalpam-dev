"""
Convert a PDF to a single UTF-8 text file using the teluguOCR pipeline
(https://github.com/Thanirex/teluguOCR): image processing + Tesseract Telugu OCR.
Saves as plain text with UTF-8 encoding.
"""
from __future__ import annotations

import os
import sys

# Ensure UTF-8 for stdout/stderr on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SCRIPT_DIR, "sri-ramanavami-pooja-vidhanam.pdf")
OUTPUT_TXT_PATH = os.path.join(SCRIPT_DIR, "sri-ramanavami-pooja-vidhanam.txt")


def rescale_frame(frame, scale=0.75):
    """Resize image by scale factor (teluguOCR rescaleFrame)."""
    import cv2 as cv
    width = int(frame.shape[1] * scale)
    height = int(frame.shape[0] * scale)
    dimensions = (width, height)
    return cv.resize(frame, dimensions, interpolation=cv.INTER_AREA)


def apply_gamma(image, gamma=1.0):
    """Apply gamma correction (teluguOCR apply_gamma)."""
    import cv2 as cv
    import numpy as np
    inv_gamma = 1.0 / gamma
    table = np.array(
        [((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]
    ).astype("uint8")
    return cv.LUT(image, table)


def adaptive_threshold(image):
    """Adaptive thresholding (teluguOCR)."""
    import cv2 as cv
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    return cv.adaptiveThreshold(
        gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 11, 2
    )


def edge_detection(image):
    """Canny edge detection (teluguOCR)."""
    import cv2 as cv
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    return cv.Canny(gray, 50, 150)


def morphological_transformation(image):
    """Morphological transform (teluguOCR)."""
    import cv2 as cv
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    _, binary = cv.threshold(gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))
    return cv.morphologyEx(binary, cv.MORPH_CLOSE, kernel)


def process_image(img, method="default"):
    """Process image for OCR using teluguOCR methods."""
    import cv2 as cv
    import numpy as np
    resized = rescale_frame(img)
    if method == "default":
        gray = cv.cvtColor(resized, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (3, 3), 0)
        gamma_corrected = apply_gamma(blur, gamma=0.3)
        _, thresh = cv.threshold(
            gamma_corrected, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU
        )
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))
        return cv.morphologyEx(thresh, cv.MORPH_CLOSE, kernel)
    if method == "adaptive_threshold":
        return adaptive_threshold(resized)
    if method == "edge_detection":
        return edge_detection(resized)
    if method == "morphological":
        return morphological_transformation(resized)
    raise ValueError(f"Unknown method: {method}")


def extract_text_from_image(image, langs="tel"):
    """Run Tesseract Telugu OCR (teluguOCR extract_text_from_image)."""
    import pytesseract
    return pytesseract.image_to_string(image, lang=langs)


def pdf_pages_to_images(pdf_path: str):
    """Convert PDF to list of BGR numpy arrays (OpenCV format)."""
    import cv2 as cv
    import numpy as np
    try:
        import fitz
    except ImportError:
        # Fallback: pdf2image like teluguOCR
        from pdf2image import convert_from_path
        pages = convert_from_path(pdf_path)
        return [cv.cvtColor(np.array(p), cv.COLOR_RGB2BGR) for p in pages]
    doc = fitz.open(pdf_path)
    images = []
    for i in range(len(doc)):
        page = doc[i]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img_bytes = pix.tobytes("png")
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv.imdecode(nparr, cv.IMREAD_COLOR)
        if img is not None:
            images.append(img)
    doc.close()
    return images


def best_text_for_image(img):
    """Run all teluguOCR methods and return text with highest character count."""
    methods = ["default", "adaptive_threshold", "edge_detection", "morphological"]
    best_text = ""
    max_len = -1
    for method in methods:
        processed = process_image(img, method=method)
        text = extract_text_from_image(processed, langs="tel")
        if text is None:
            text = ""
        text = text.strip()
        if len(text) > max_len:
            max_len = len(text)
            best_text = text
    return best_text


def main() -> None:
    if not os.path.isfile(PDF_PATH):
        print(f"Error: PDF not found: {PDF_PATH}", file=sys.stderr)
        sys.exit(1)

    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
        import pytesseract
    except ImportError as e:
        print(f"Error: Missing dependency: {e}", file=sys.stderr)
        print("Install: pip install opencv-python-headless numpy pytesseract PyMuPDF", file=sys.stderr)
        sys.exit(1)

    # Optional: set Tesseract path on Windows
    if sys.platform == "win32":
        for path in (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LocalAppData%\Tesseract-OCR\tesseract.exe"),
        ):
            if os.path.isfile(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break

    tesseract_ok = False
    try:
        pytesseract.get_tesseract_version()
        tesseract_ok = True
    except Exception:
        print("Tesseract not found. Using PDF embedded text (install Tesseract for teluguOCR pipeline).", file=sys.stderr)

    full_text = ""
    if tesseract_ok:
        print(f"Loading PDF: {PDF_PATH}")
        try:
            images = pdf_pages_to_images(PDF_PATH)
        except Exception as e:
            print(f"Error converting PDF to images: {e}", file=sys.stderr)
            sys.exit(1)
        if not images:
            print("Error: No pages found in PDF.", file=sys.stderr)
            sys.exit(1)
        total = len(images)
        print(f"Pages: {total}. Running Telugu OCR (teluguOCR pipeline)...")
        page_texts = []
        for i, img in enumerate(images):
            try:
                text = best_text_for_image(img)
            except Exception as e:
                print(f"Warning: OCR failed for page {i + 1}: {e}", file=sys.stderr)
                text = ""
            page_texts.append(f"--- Page {i + 1} ---\n\n{text}")
            print(f"  Page {i + 1}/{total} done.")
        full_text = "\n\n".join(page_texts)
    else:
        # Fallback: extract embedded text with PyMuPDF (UTF-8)
        try:
            import fitz
        except ImportError:
            print("Error: PyMuPDF required when Tesseract is not installed. pip install PyMuPDF", file=sys.stderr)
            sys.exit(1)
        print(f"Loading PDF (embedded text): {PDF_PATH}")
        doc = fitz.open(PDF_PATH)
        parts = []
        for i in range(len(doc)):
            parts.append(f"--- Page {i + 1} ---\n\n{doc[i].get_text()}")
        full_text = "\n\n".join(parts)
        doc.close()
        print(f"Extracted {len(parts)} pages.")

    try:
        with open(OUTPUT_TXT_PATH, "w", encoding="utf-8") as f:
            f.write(full_text)
    except OSError as e:
        print(f"Error writing file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved: {OUTPUT_TXT_PATH} (UTF-8)")


if __name__ == "__main__":
    main()
