# invoice_parser.py
from backend.app.parser.table_parser import extract_line_items_layout


import re

LABELS = {
    "invoice_number": ["invoice no", "invoice number", "bill no", "inv #"],
    "invoice_date": ["invoice date", "date", "bill date", "date issued"],
    "customer_name": ["bill to", "billed to", "customer", "client"],
    "total_amount": ["grand total", "total", "amount due"]
}


# =========================
# HELPERS
# =========================

def sort_ocr(ocr_data):
    return sorted(ocr_data, key=lambda x: (x["y"], x["x"]))


def group_rows(ocr_data, y_threshold=20):
    rows, current = [], []
    last_y = None

    for item in ocr_data:
        if last_y is None or abs(item["y"] - last_y) < y_threshold:
            current.append(item)
        else:
            rows.append(current)
            current = [item]

        last_y = item["y"]

    if current:
        rows.append(current)

    return rows


def row_to_text(row):
    return " ".join([c["text"] for c in sorted(row, key=lambda x: x["x"])])


# =========================
# VALIDATORS
# =========================

def is_valid_invoice_number(val):
    if not val:
        return False

    val = val.strip()

    # ❌ Reject phone numbers
    if re.fullmatch(r'\d{10}', val):
        return False

    # ❌ Reject pure words
    if val.isalpha():
        return False

    # ✅ Must contain digit + length
    return bool(re.search(r'\d', val) and len(val) >= 5)


def is_valid_name(text):
    if not text:
        return False

    text = text.strip()

    # ❌ Reject address-like
    if re.search(r'\d{3,}', text):
        return False

    # ❌ Reject keywords
    bad_words = ["invoice", "date", "gst", "total"]
    if any(w in text.lower() for w in bad_words):
        return False

    return len(text) > 2


def is_valid_amount(val):
    try:
        num = float(val.replace(",", ""))
        return num > 100  # avoid wrong small values
    except:
        return False


def clean(val):
    return val.replace(":", "").strip()


# =========================
# EXTRACTORS
# =========================

def extract_invoice_number(lines):
    for line in lines:
        l = line.lower()

        if any(k in l for k in LABELS["invoice_number"]):
            parts = re.split(r'[:\-]', line, 1)
            if len(parts) > 1:
                val = clean(parts[1])

                if is_valid_invoice_number(val):
                    return val

    return None


def extract_date(lines):
    for line in lines:
        match = re.search(
            r'\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            line
        )
        if match:
            return match.group(0)

    return None


def extract_customer(lines):
    for i, line in enumerate(lines):
        l = line.lower()

        if any(k in l for k in LABELS["customer_name"]):

            # Case 1: inline
            parts = re.split(r'[:\-]', line, 1)
            if len(parts) > 1:
                val = clean(parts[1])
                if is_valid_name(val):
                    return val

            # Case 2: next line (MOST IMPORTANT FIX)
            if i + 1 < len(lines):
                val = lines[i + 1].strip()

                if is_valid_name(val):
                    return val

    return None


def extract_total(lines):
    best = None

    for line in lines:
        nums = re.findall(r'[\d,]+(?:\.\d+)?', line)
        if not nums:
            continue

        val = nums[-1]
        l = line.lower()

        if not is_valid_amount(val):
            continue

        if "grand total" in l:
            return val

        if "amount due" in l:
            best = val

        elif "total" in l:
            best = val

    return best


# =========================
# MAIN
# =========================

def parse_invoice(ocr_data):

    if not ocr_data:
        return {}

    ocr_data = sort_ocr(ocr_data)
    rows = group_rows(ocr_data)
    lines = [row_to_text(r) for r in rows]

    result = {
        "invoice_number": extract_invoice_number(lines),
        "invoice_date": extract_date(lines),
        "customer_name": extract_customer(lines),
        "total_amount": extract_total(lines),
        "email": None,
        "phone_number": None,
        "line_items": extract_line_items_layout(ocr_data),
        "confidence": {}
    }

    full_text = " ".join(lines)

    # Email
    m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', full_text)
    if m:
        result["email"] = m.group(0)

    # Phone
    m = re.search(r'\b[6-9]\d{9}\b', full_text)
    if m:
        result["phone_number"] = m.group(0)

    # Confidence
    for k in result:
        if k not in ["confidence", "line_items"] and result[k]:
            result["confidence"][k] = 0.9

    result["overall_confidence"] = round(
        sum(result["confidence"].values()) / len(result["confidence"])
        if result["confidence"] else 0,
        2
    )

    return result
