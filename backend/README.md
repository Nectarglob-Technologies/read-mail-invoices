# Outlook Invoice Processor (Open Source)

Reads invoices from Outlook emails (PDF / scanned images),
extracts invoice data using OCR, and stores structured JSON.

## Setup
1. Create Azure App → Mail.Read permission
2. Copy `.env.example` → `.env`
3. Install dependencies
4. Run `python app/main.py`

## Output
JSON files in `data/output_json/`
