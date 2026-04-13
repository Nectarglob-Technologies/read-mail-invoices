# llm_extractor.py

import json
import re
from openai import OpenAI
from backend.app.core.config import OPENAI_API_KEY, LLM_MODEL


# =========================
# INIT CLIENT
# =========================
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is not loaded from .env")

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================
# MAIN FUNCTION
# =========================
def extract_with_llm(full_text):
    try:
        prompt = f"""
        You are an invoice data extraction engine.

        Extract the following fields from the invoice text.

        Return ONLY valid JSON (no explanation, no markdown):

        {{
        "invoice_number": "",
        "invoice_date": "",
        "customer_name": "",
        "total_amount": ""
        }}

        Rules:
        - Do NOT guess values
        - If not found, return null
        - Remove labels like "Invoice No", "Date", etc.
        - Return clean values only

        Invoice Text:
        {full_text[:4000]}
        """

        response = client.chat.completions.create(
            model=LLM_MODEL or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract structured data from invoices."},
                {"role": "user", "content": prompt}
            ]
            # ✅ REMOVED temperature (fixes your error)
        )

        content = response.choices[0].message.content.strip()

        # ==========================
        # CLEAN RESPONSE
        # ==========================
        content = clean_json_response(content)

        # ==========================
        # SAFE JSON LOAD
        # ==========================
        data = json.loads(content)

        return normalize_output(data)

    except Exception as e:
        print("❌ LLM ERROR:", str(e))
        return {}


# =========================================
# CLEAN LLM RESPONSE (VERY IMPORTANT)
# =========================================
def clean_json_response(content):
    """
    Removes markdown, extra text, etc.
    """

    # Remove ```json blocks
    content = re.sub(r"```json", "", content, flags=re.IGNORECASE)
    content = re.sub(r"```", "", content)

    # Trim before first {
    if "{" in content:
        content = content[content.index("{"):]

    # Trim after last }
    if "}" in content:
        content = content[:content.rindex("}") + 1]

    return content.strip()


# =========================================
# NORMALIZE OUTPUT
# =========================================
def normalize_output(data):
    """
    Ensures consistent clean output
    """

    def clean(val):
        if val in ["", "null", None]:
            return None

        val = str(val).strip()

        # remove currency symbols
        val = re.sub(r'[₹$,]', '', val)

        return val

    return {
        "invoice_number": clean(data.get("invoice_number")),
        "invoice_date": clean(data.get("invoice_date")),
        "customer_name": clean(data.get("customer_name")),
        "total_amount": clean(data.get("total_amount")),
    }

def extract_table_with_llm(text):
    try:
        prompt = f"""
        Extract invoice line items.

        Return JSON:

        [
        {{
            "description": "",
            "quantity": "",
            "rate": "",
            "amount": ""
        }}
        ]

        Rules:
        - Extract ALL rows
        - Ignore totals/taxes
        - Return clean values

        Invoice:
        {text[:4000]}
        """

        response = client.chat.completions.create(
            model=LLM_MODEL or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.choices[0].message.content.strip()
        content = clean_json_response(content)

        return json.loads(content)

    except Exception as e:
        print("❌ LLM TABLE ERROR:", str(e))
        return []

