import re
from collections import defaultdict


# =========================
# STEP 1: GROUP ROWS (Y CLUSTERING)
# =========================
def group_rows_by_y(ocr_data, y_threshold=20):
    rows = []
    current = []
    last_y = None

    for item in sorted(ocr_data, key=lambda x: (x["y"], x["x"])):

        if last_y is None or abs(item["y"] - last_y) < y_threshold:
            current.append(item)
        else:
            rows.append(current)
            current = [item]

        last_y = item["y"]

    if current:
        rows.append(current)

    return rows


# =========================
# STEP 2: DETECT HEADER
# =========================
def detect_header_row(rows):
    keywords = ["description", "qty", "quantity", "rate", "amount", "price"]

    for i, row in enumerate(rows):
        text = " ".join([c["text"].lower() for c in row])

        if sum(k in text for k in keywords) >= 2:
            return i

    return None


# =========================
# STEP 3: FIND COLUMN POSITIONS (X ALIGNMENT)
# =========================
def get_column_positions(header_row):
    cols = {}

    for cell in header_row:
        text = cell["text"].lower()

        if "desc" in text:
            cols["description"] = cell["x"]
        elif "qty" in text:
            cols["quantity"] = cell["x"]
        elif "rate" in text or "price" in text:
            cols["rate"] = cell["x"]
        elif "amount" in text:
            cols["amount"] = cell["x"]

    return cols


# =========================
# STEP 4: MAP ROW TO COLUMNS
# =========================
def map_row_to_item(row, col_positions):

    item = {
        "description": "",
        "quantity": None,
        "rate": None,
        "amount": None
    }

    for cell in row:
        x = cell["x"]
        text = cell["text"]

        # Find closest column
        closest_col = min(col_positions, key=lambda k: abs(x - col_positions[k]))

        if closest_col == "description":
            item["description"] += " " + text

        elif closest_col == "quantity":
            item["quantity"] = text

        elif closest_col == "rate":
            item["rate"] = text

        elif closest_col == "amount":
            item["amount"] = text

    item["description"] = item["description"].strip()

    return item


# =========================
# STEP 5: STOP CONDITIONS
# =========================
def is_summary_row(row):
    text = " ".join([c["text"].lower() for c in row])

    return any(k in text for k in ["total", "gst", "tax", "grand"])


# =========================
# MAIN FUNCTION
# =========================
def extract_line_items_layout(ocr_data):

    rows = group_rows_by_y(ocr_data)

    header_idx = detect_header_row(rows)

    if header_idx is None:
        return []

    header_row = rows[header_idx]
    col_positions = get_column_positions(header_row)

    if not col_positions:
        return []

    items = []

    for row in rows[header_idx + 1:]:

        if is_summary_row(row):
            break

        item = map_row_to_item(row, col_positions)

        # validation
        if item["description"] and item["amount"]:
            items.append(item)

        if len(items) >= 50:
            break

    return items
