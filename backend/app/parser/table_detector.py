import re


def is_header(line):
    keywords = ["description", "qty", "quantity", "rate", "price", "amount"]
    line = line.lower()
    return sum(1 for k in keywords if k in line) >= 2


def is_noise(line):
    return any(x in line.lower() for x in [
        "total", "gst", "cgst", "sgst", "tax", "grand"
    ])


def extract_numbers(line):
    return re.findall(r'[\d,]+(?:\.\d+)?', line)


def detect_table(text_lines):

    items = []
    start_idx = None

    # ---------------- STEP 1: FIND HEADER ----------------
    for i, line in enumerate(text_lines):
        if is_header(line):
            start_idx = i
            break

    if start_idx is None:
        return []  # no table found

    # ---------------- STEP 2: PROCESS ROWS ----------------
    buffer = []

    for line in text_lines[start_idx + 1:]:

        if is_noise(line):
            break  # stop at totals

        if not line.strip():
            continue

        buffer.append(line.strip())

        # ---------------- STEP 3: GROUP INTO ROWS ----------------
        if len(buffer) >= 2:

            combined = " ".join(buffer)
            nums = extract_numbers(combined)

            if len(nums) >= 2:
                item = {
                    "description": buffer[0],
                    "qty": None,
                    "rate": None,
                    "amount": nums[-1]
                }

                # try extracting qty & rate
                if len(nums) == 3:
                    item["qty"] = nums[0]
                    item["rate"] = nums[1]
                elif len(nums) >= 4:
                    item["qty"] = nums[0]
                    item["rate"] = nums[1]

                items.append(item)

                buffer = []  # reset after forming row

        # safety limit
        if len(items) >= 25:
            break

    return items
