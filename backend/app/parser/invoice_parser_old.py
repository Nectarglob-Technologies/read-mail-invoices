import re


def clean_amount(val):
    try:
        return float(val.replace(",", ""))
    except:
        return None

def normalize_text(text_lines):
    """
    Convert vertical + broken OCR text into structured lines
    """
    normalized = []

    i = 0
    while i < len(text_lines):
        line = text_lines[i].strip()

        # Merge vertical key-value pairs
        if i + 1 < len(text_lines):
            next_line = text_lines[i + 1].strip()

            # Case: "Invoice Number" + "INV-10012"
            if (
                len(line) < 40 and
                len(next_line) < 40 and
                not any(x in next_line.lower() for x in ["invoice", "date", "total"])
            ):
                merged = f"{line}: {next_line}"
                normalized.append(merged)
                i += 2
                continue

        normalized.append(line)
        i += 1

    return normalized


def parse_invoice(text_lines):
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

    # ---------------- INVOICE NUMBER ----------------
    patterns = [
        r'(?:Invoice\s*No\.?|Invoice\s*Number|Bill\s*No)\s*[:\-]?\s*([A-Za-z0-9\/\-]+)',
        r'Invoice\s*#\s*([A-Za-z0-9\/\-]+)'
    ]

    patterns = [
        r'(?:Invoice\s*(?:No|Number|#)|Bill\s*No)[\s:\-]*([A-Za-z0-9\/\-]+)',
        r'Inv[\s\-]*No[\s:\-]*([A-Za-z0-9\/\-]+)'
    ]


    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            result["invoice_number"] = m.group(1)
            result["confidence"]["invoice_number"] = 0.9
            break

    # ---------------- DATE ----------------
    date_patterns = [
        r'(?:Invoice\s*Date|Date)[\s:\-]*([0-9]{4}-[0-9]{2}-[0-9]{2})',
        r'(?:Invoice\s*Date|Date)[\s:\-]*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4})',
        r'(\d{1,2}-[A-Za-z]{3}-\d{4})',
        r'([A-Za-z]{3}\s\d{1,2},\s\d{4})'
    ]

    date_patterns = [
        r'(?:Invoice\s*Date|Date\s*Issued|Date)[\s:\-]*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4})',
        r'(?:Invoice\s*Date|Date)[\s:\-]*([0-9]{4}-[0-9]{2}-[0-9]{2})',
    ]


    for p in date_patterns:
        m = re.search(p, text)
        if m:
            result["invoice_date"] = m.group(1)
            result["confidence"]["invoice_date"] = 0.85
            break

    # ---------------- CUSTOMER ----------------
    customer_patterns = [
        r'Customer\s*Name\s*[:\-]?\s*(.*?)\s*(?:Bill|Invoice|Date)',
        r'Customer\s*[:\-]?\s*(.*?)\s*(?:Bill|Invoice|Date)',
        r'Bill\s*To\s*[:\-]?\s*(.*?)\s*Invoice',
        r'M/S\s*(.*?)\s*(?:Challan|Address)'
    ]

    for pattern in customer_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            name = re.sub(r'^[^\w]+', '', name)

            if 3 < len(name) < 60 and not re.search(
                r'invoice|date|total|amount|number', name.lower()
            ):
                result["customer_name"] = name
                result["confidence"]["customer_name"] = 0.8
                break

    # ---------------- EMAIL ----------------
    m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if m:
        result["email"] = m.group(0)
        result["confidence"]["email"] = 0.95

    # ---------------- PHONE ----------------
    m = re.search(r'Phone\s*[:\-]?\s*(\d{10})', text, re.IGNORECASE)
    if not m:
        m = re.search(r'\b[6-9]\d{9}\b', text)

    if m:
        result["phone_number"] = m.group(1 if len(m.groups()) else 0)
        result["confidence"]["phone"] = 0.9

    # ---------------- TOTAL ----------------
    total_amount = None

    # 1️⃣ Grand total
    m = re.search(
        r'(Grand\s*Total|Net\s*Total|Total\s*Amount)[^\d]*([\d,]+(?:\.\d{1,2})?)',
        text,
        re.IGNORECASE
    )
    if m:
        total_amount = m.group(2)

    # 2️⃣ GST logic
    if not total_amount:
        taxable = None
        gst_total = 0

        for i, line in enumerate(text_lines):
            if any(x in line.lower() for x in ["igst", "cgst", "sgst"]):
                nums = re.findall(r'[\d,]+(?:\.\d+)?', line)

                if nums:
                    gst_total += clean_amount(nums[-1]) or 0

                if i > 0 and not taxable:
                    prev_nums = re.findall(r'[\d,]+(?:\.\d+)?', text_lines[i-1])
                    if prev_nums:
                        taxable = clean_amount(prev_nums[-1])

        if taxable:
            total_amount = str(round(taxable + gst_total))

    # 3️⃣ Simple total
    if not total_amount:
        m = re.search(
            r'\bTotal\b\s*(?:Rs\.?|INR|\$)?\s*([\d,]+(?:\.\d+)?)',
            text,
            re.IGNORECASE
        )
        if m:
            total_amount = m.group(1)

    result["total_amount"] = total_amount
    if total_amount:
        result["confidence"]["total_amount"] = 0.9

    # ---------------- LINE ITEMS (🔥 BIG UPGRADE) ----------------
    items = []

    for line in text_lines:
        # Detect rows like: item qty price total
        if re.search(r'\d+\s*x\s*\d+', line) or re.search(r'\d+\.\d{2}', line):
            nums = re.findall(r'[\d,]+(?:\.\d+)?', line)

            if len(nums) >= 2:
                items.append({
                    "raw": line,
                    "amount": nums[-1]
                })

    result["line_items"] = items[:20]

    # ---------------- OVERALL CONFIDENCE ----------------
    if result["confidence"]:
        result["overall_confidence"] = round(
            sum(result["confidence"].values()) / len(result["confidence"]),
            2
        )
    else:
        result["overall_confidence"] = 0

    return result
