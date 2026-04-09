from backend.app.parser.field_detector import (
    detect_invoice_number,
    detect_date,
    detect_total,
    detect_customer
)

from backend.app.parser.table_detector import detect_table

import re


def clean_amount(val):
    try:
        return float(val.replace(",", ""))
    except:
        return None


# ✅ FINAL NORMALIZATION (SAFE + CONTROLLED)
def normalize_text(text_lines):
    normalized = []

    i = 0
    while i < len(text_lines):
        line = text_lines[i].strip()

        if i + 1 < len(text_lines):
            next_line = text_lines[i + 1].strip()

            # ✅ Only merge true key-value (avoid bad merges)
            if (
                ":" not in line and
                len(line) < 25 and
                len(next_line) < 40 and
                not re.search(r'(invoice|date|total|gst|amount|description)', next_line.lower())
            ):
                normalized.append(f"{line}: {next_line}")
                i += 2
                continue

        normalized.append(line)
        i += 1

    return normalized

def parse_invoice(text_lines):

    # ✅ Normalize
    text_lines = normalize_text(text_lines)

    print("\n====== NORMALIZED TEXT ======")
    for line in text_lines[:30]:
        print("→", line)
    print("============================\n")

    text = " ".join(text_lines)

    result = {
        "invoice_number": None,
        "invoice_date": None,
        "customer_name": None,
        "email": None,
        "phone_number": None,
        "total_amount": None,
        "line_items": [],
        "confidence": {}
    }

    # =========================================================
    # ✅ STEP 1: AI-LIKE DETECTION (PRIMARY)
    # =========================================================

    result["invoice_number"] = detect_invoice_number(text_lines)
    result["invoice_date"] = detect_date(text_lines)
    result["customer_name"] = detect_customer(text_lines)
    result["total_amount"] = detect_total(text_lines)
    result["line_items"] = detect_table(text_lines)

    # =========================================================
    # ✅ STEP 2: REGEX FALLBACK (ONLY IF MISSING)
    # =========================================================

    # Invoice number fallback
    if not result["invoice_number"]:
        m = re.search(r'(?:Invoice\s*(?:No|Number|#)|Bill\s*No)[\s:\-]*([A-Za-z0-9\/\-]+)', text, re.IGNORECASE)
        if m:
            result["invoice_number"] = m.group(1)

    # Date fallback
    if not result["invoice_date"]:
        m = re.search(r'([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4})', text)
        if m:
            result["invoice_date"] = m.group(1)

    # Customer fallback
    if not result["customer_name"]:
        for i, line in enumerate(text_lines):
            if "bill to" in line.lower():
                if i + 1 < len(text_lines):
                    result["customer_name"] = text_lines[i + 1].strip()
                    break

    # Total fallback
    if not result["total_amount"]:
        m = re.search(r'(Total)[^\d]*([\d,]+(?:\.\d{1,2})?)', text, re.IGNORECASE)
        if m:
            result["total_amount"] = m.group(2)

    # =========================================================
    # ✅ STEP 3: EMAIL & PHONE (KEEP FROM PHASE 1)
    # =========================================================

    m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if m:
        result["email"] = m.group(0)

    m = re.search(r'\b[6-9]\d{9}\b', text)
    if m:
        result["phone_number"] = m.group(0)

    # =========================================================
    # ✅ STEP 4: CONFIDENCE
    # =========================================================

    for key in result:
        if key not in ["confidence", "line_items"] and result[key]:
            result["confidence"][key] = 0.9

    result["overall_confidence"] = round(
        sum(result["confidence"].values()) / len(result["confidence"])
        if result["confidence"] else 0,
        2
    )

    return result
