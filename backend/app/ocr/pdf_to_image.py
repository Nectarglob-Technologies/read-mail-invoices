import fitz  # PyMuPDF
import os
from backend.app.core.config import IMAGES_DIR


def pdf_to_images(pdf_path: str):
    try:
        print(f"Converting PDF: {pdf_path}")

        # Ensure directory exists
        os.makedirs(IMAGES_DIR, exist_ok=True)

        doc = fitz.open(pdf_path)
        image_paths = []

        for i, page in enumerate(doc):
            # 🔥 HIGH DPI (critical for OCR accuracy)
            zoom = 4  # ~300 DPI
            matrix = fitz.Matrix(zoom, zoom)

            pix = page.get_pixmap(matrix=matrix, alpha=False)

            filename = os.path.basename(pdf_path).replace(".pdf", "")

            output_path = os.path.join(
                IMAGES_DIR,
                f"{filename}_page_{i + 1}.png"  # cleaner numbering
            )

            # 🔥 Save as PNG (lossless)
            pix.save(output_path)

            print(f"Saved: {output_path}")

            image_paths.append(output_path)

        doc.close()

        print(f"Total pages converted: {len(image_paths)}")

        return image_paths

    except Exception as e:
        print("PDF ERROR:", e)
        return []
