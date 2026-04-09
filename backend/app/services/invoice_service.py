import os
import tempfile

from backend.app.ocr.pdf_to_image import pdf_to_images
from backend.app.ocr.ocr_engine import extract_text
from backend.app.parser.invoice_parser import parse_invoice
from backend.app.parser.llm_extractor import extract_with_llm
from backend.app.storage.json_writer import save_json

from backend.app.utils.logger import get_logger
from backend.app.jobs.job_runner import create_job, update_job

logger = get_logger()


# ===============================
# CONFIDENCE CHECK
# ===============================
def is_low_confidence(result):
    critical_fields = [
        "invoice_number",
        "invoice_date",
        "customer_name",
        "total_amount"
    ]

    missing = [f for f in critical_fields if not result.get(f)]

    if len(missing) >= 2:
        logger.info(f"LOW CONFIDENCE → Missing fields: {missing}")
        return True

    return False


# ===============================
# MAIN SERVICE
# ===============================
def process_invoice(file_bytes, filename="invoice.pdf"):

    job_id, _ = create_job(filename)

    try:
        logger.info(f"Start processing | Job ID: {job_id}")

        # ================= SAVE TEMP FILE =================
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            file_path = tmp.name

        logger.info(f"Temp PDF: {file_path}")

        # ================= PDF → IMAGES =================
        images = pdf_to_images(file_path)

        if not images:
            raise Exception("No images generated from PDF")

        # ================= OCR =================
        all_ocr_data = []
        confidences = []
        full_text_parts = []

        for img in images:
            result = extract_text(img)

            if not result or "ocr_data" not in result:
                continue

            all_ocr_data.extend(result.get("ocr_data", []))
            confidences.append(result.get("confidence", 0))

            # collect full text
            for item in result.get("ocr_data", []):
                full_text_parts.append(item.get("text", ""))

        logger.info(f"OCR ITEMS: {len(all_ocr_data)}")

        if not all_ocr_data:
            raise Exception("OCR returned empty data")

        full_text = " ".join(full_text_parts)

        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        # ================= SMART PARSER =================
        invoice_data = parse_invoice(all_ocr_data)

        # ================= LLM FALLBACK =================
        if is_low_confidence(invoice_data):
            logger.info("Triggering LLM fallback...")

            llm_result = extract_with_llm(full_text)

            # Merge (LLM fills missing only)
            for key, value in llm_result.items():
                if not invoice_data.get(key) and value:
                    invoice_data[key] = value

        invoice_data["ocr_confidence"] = round(avg_conf, 3)

        logger.info(f"Final Parsed Data: {invoice_data}")

        # ================= SAVE JSON =================
        json_path = save_json(invoice_data)

        # ================= CLEANUP =================
        if os.path.exists(file_path):
            os.remove(file_path)

        update_job(job_id, "COMPLETED", result={
            "data": invoice_data,
            "json_path": json_path
        })

        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "data": invoice_data,
            "json_path": json_path
        }

    except Exception as e:
        logger.error(f"SERVICE ERROR | Job ID: {job_id} | {str(e)}")

        update_job(job_id, "FAILED", error=str(e))

        return {
            "job_id": job_id,
            "status": "FAILED",
            "error": str(e)
        }
