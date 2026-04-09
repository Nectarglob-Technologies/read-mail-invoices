from backend.app.email import EmailReader
from backend.app.services.invoice_service import process_invoice


def process_email_invoices():
    reader = EmailReader()

    files = reader.fetch_latest_invoice_attachments()

    results = []

    for file_path in files:
        with open(file_path, "rb") as f:
            result = process_invoice(f.read(), file_path)
            results.append(result)

    return results
