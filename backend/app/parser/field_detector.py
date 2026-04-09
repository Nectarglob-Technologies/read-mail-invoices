import re


def find_value_after_keyword(text_lines, keywords):
    """
    Finds value after keywords (works for vertical + horizontal)
    """
    for i, line in enumerate(text_lines):
        lower = line.lower()

        for key in keywords:
            if key in lower:

                # Case 1: "Date: 2026-01-01"
                m = re.search(r'[:\-]\s*(.+)', line)
                if m:
                    return m.group(1).strip()

                # Case 2: next line value
                if i + 1 < len(text_lines):
                    return text_lines[i + 1].strip()

    return None


def detect_invoice_number(text_lines):
    val = find_value_after_keyword(
        text_lines,
        ["invoice number", "invoice no", "bill no", "inv no"]
    )

    if val:
        return val

    # fallback regex
    text = " ".join(text_lines)
    m = re.search(r'\b[A-Z0-9\/\-]{5,}\b', text)
    return m.group(0) if m else None


def detect_date(text_lines):
    val = find_value_after_keyword(
        text_lines,
        ["invoice date", "date issued", "date"]
    )

    if val:
        return val

    return None


def detect_total(text_lines):
    # priority keywords
    for key in ["grand total", "net total", "total"]:
        val = find_value_after_keyword(text_lines, [key])
        if val:
            m = re.search(r'[\d,]+(?:\.\d+)?', val)
            if m:
                return m.group(0)

    return None


def detect_customer(text_lines):
    val = find_value_after_keyword(
        text_lines,
        ["bill to", "customer", "buyer"]
    )

    if val and len(val) > 3:
        return val

    return None
