from fastapi import FastAPI, UploadFile, File
from backend.app.services.invoice_service import process_invoice
from backend.app.jobs.job_runner import get_job

app = FastAPI(
    title="Invoice OCR API",
    description="Extract invoice data using OCR (EasyOCR + PaddleOCR fallback)",
    version="1.0"
)


# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def health():
    return {
        "status": "running",
        "message": "Invoice OCR API is up"
    }


# -----------------------------
# Extract Invoice
# -----------------------------
@app.post("/extract")
async def extract_invoice(file: UploadFile = File(...)):
    try:
        # Read file
        file_bytes = await file.read()

        # ✅ Validate file
        if not file_bytes:
            return {
                "status": "FAILED",
                "error": "Empty file uploaded"
            }

        # Process invoice
        result = process_invoice(file_bytes, file.filename)

        return result

    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e)
        }


# -----------------------------
# Job Status API (VERY IMPORTANT)
# -----------------------------
@app.get("/job/{job_id}")
def check_job(job_id: str):
    try:
        job = get_job(job_id)

        if not job:
            return {
                "status": "NOT_FOUND",
                "job_id": job_id
            }

        return job

    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e)
        }
