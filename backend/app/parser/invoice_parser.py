# invoice_parser.py

import re
from backend.app.parser.llm_extractor import extract_with_llm

# =========================================
# LABELS
# =========================================

LABELS = {
    "invoice_number": ["invoice no", "invoice number", "bill no", "inv #"],
    "invoice_date": ["invoice date", "date", "bill date"],
    "customer_name": ["bill to", "customer", "client"],
    "total_amount": ["grand total", "total"]
}

# =========================================
# HELPERS
# =========================================

def sort_ocr(ocr_data):
    return sorted(ocr_data, key=lambda x: (x["y"], x["x"]))


def group_rows(ocr_data, y_threshold=15):
    rows, current_row = [], []
    last_y = None

    for item in ocr_data:
        if last_y is None or abs(item["y"] - last_y) < y_threshold:
            current_row.append(item)
        else:
            rows.append(current_row)
            current_row = [item]

        last_y = item["y"]

    if current_row:
        rows.append(current_row)

    return rows


def row_to_text(row):
    return " ".join([c["text"] for c in sorted(row, key=lambda x: x["x"])])


# =========================================
# SCORING
# =========================================

def score(label=False, numeric=False, date=False, position=0):
    s = 0
    if label:
        s += 0.5
    if numeric:
        s += 0.2
    if date:
        s += 0.3
    return s + position


# =========================================
# EXTRACTION FUNCTIONS
# =========================================

def extract_invoice_number(lines):
    candidates = []

    for line in lines:
        l = line.lower()

        # Label based
        if any(k in l for k in LABELS["invoice_number"]):
            parts = re.split(r'[:\-]', line, 1)
            if len(parts) > 1:
                val = parts[1].strip()
                candidates.append((val, score(True, True, position=0.3)))

        # Pattern fallback
        match = re.search(r'\b[A-Z0-9\/\-]{5,}\b', line)
        if match:
            candidates.append((match.group(0), score(numeric=True)))

    return max(candidates, key=lambda x: x[1])[0] if candidates else None


def extract_date(lines):
    candidates = []

    for line in lines:
        l = line.lower()

        if any(k in l for k in LABELS["invoice_date"]):
            parts = re.split(r'[:\-]', line, 1)
            if len(parts) > 1:
                candidates.append((parts[1].strip(), score(True, date=True)))

        match = re.search(r'\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line)
        if match:
            candidates.append((match.group(0), score(date=True)))

    return max(candidates, key=lambda x: x[1])[0] if candidates else None


def extract_customer(lines):
    candidates = []

    for i, line in enumerate(lines):
        l = line.lower()

        if any(k in l for k in LABELS["customer_name"]):

            # Case 1: inline → "Customer: ABC Pvt Ltd"
            parts = re.split(r'[:\-]', line, 1)
            if len(parts) > 1:
                val = parts[1].strip()

                if is_valid_name(val):
                    candidates.append((val, score(True, position=0.4)))

            # Case 2: next line → "Bill To" → next line name
            if i + 1 < len(lines):
                val = lines[i + 1].strip()

                if is_valid_name(val):
                    candidates.append((val, score(True, position=0.3)))

    return max(candidates, key=lambda x: x[1])[0] if candidates else None


def is_valid_name(text):
    if not text:
        return False

    # Reject garbage
    if re.search(r'\d{5,}', text):
        return False

    if any(k in text.lower() for k in ["invoice", "date", "gst", "total", "bill no"]):
        return False

    if len(text) < 3:
        return False

    return True


def extract_total(lines):
    candidates = []

    for line in lines:
        nums = re.findall(r'[\d,]+(?:\.\d+)?', line)

        if nums:
            val = nums[-1]
            l = line.lower()

            if "grand total" in l:
                candidates.append((val, 1.0))
            elif "total" in l:
                candidates.append((val, 0.8))
            else:
                candidates.append((val, 0.3))

    return max(candidates, key=lambda x: x[1])[0] if candidates else None


# =========================================
# MAIN PARSER
# =========================================

def parse_invoice(ocr_data):

    if not ocr_data:
        return {}

    # Step 1: structure OCR
    ocr_data = sort_ocr(ocr_data)
    rows = group_rows(ocr_data)
    lines = [row_to_text(r) for r in rows]

    # Step 2: extract fields
    result = {
        "invoice_number": extract_invoice_number(lines),
        "invoice_date": extract_date(lines),
        "customer_name": extract_customer(lines),
        "total_amount": extract_total(lines),
        "email": None,
        "phone_number": None,
        "line_items": [],
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

    # =========================================
    # 🔥 LLM FALLBACK (ONLY IF NEEDED)
    # =========================================

    critical = ["invoice_number", "invoice_date", "customer_name", "total_amount"]
    missing = [k for k in critical if not result[k]]

    if len(missing) >= 2:
        print("⚠️ Using LLM fallback for:", missing)

        llm_data = extract_with_llm(full_text[:4000])

        for field in missing:
            if llm_data.get(field):
                result[field] = llm_data[field]
                result["confidence"][field] = 0.95

    # =========================================
    # CONFIDENCE
    # =========================================

    for k in result:
        if k not in ["confidence", "line_items"] and result[k]:
            result["confidence"][k] = result["confidence"].get(k, 0.9)

    result["overall_confidence"] = round(
        sum(result["confidence"].values()) / len(result["confidence"])
        if result["confidence"] else 0,
        2
    )

    return result
