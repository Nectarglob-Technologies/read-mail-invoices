import os

from backend.app.services.invoice_service import process_invoice
from backend.app.utils.logger import get_logger

logger = get_logger()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def extract_invoice_data(uploaded_file):
    try:
        # ---------------- VALIDATION ----------------
        if uploaded_file is None:
            raise Exception("No file uploaded")

        if not uploaded_file.name.lower().endswith(".pdf"):
            raise Exception("Only PDF files are supported")

        # ---------------- SAFE FILE NAME ----------------
        filename = os.path.basename(uploaded_file.name)
        file_location = os.path.join(UPLOAD_FOLDER, filename)

        logger.info(f"Saving file: {file_location}")

        with open(file_location, "wb") as buffer:
            buffer.write(uploaded_file.getbuffer())

        logger.info(f"PDF Saved: {file_location}")

        # ---------------- CALL SERVICE ----------------
        with open(file_location, "rb") as f:
            result = process_invoice(f.read(), filename)

        return result

    except Exception as e:
        logger.error(f"MAIN ERROR: {str(e)}")

        return {
            "status": "FAILED",
            "error": str(e)
        }
