import streamlit as st
import sys
import os

# Fix imports
sys.path.append(os.path.abspath("."))

from backend.app.main import extract_invoice_data

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="Invoice Extractor",
    layout="centered"
)

st.title("📄 Invoice Data Extractor")
st.markdown("Upload your invoice PDF and extract key details instantly.")

# -----------------------------
# File Upload Section
# -----------------------------
uploaded_file = st.file_uploader("📂 Upload Invoice PDF", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ PDF Uploaded Successfully")

    if st.button("🚀 Extract Data"):

        with st.spinner("Processing... ⏳"):
            result = extract_invoice_data(uploaded_file)

        # -----------------------------
        # Error Handling
        # -----------------------------
        if result.get("status") == "FAILED" or "error" in result:
            st.error(result.get("error", "Unknown error occurred"))

        else:
            data = result.get("data", {})

            st.success("✅ Extraction Completed")

            # -----------------------------
            # Job Info (optional)
            # -----------------------------
            if "job_id" in result:
                st.caption(f"🆔 Job ID: {result['job_id']}")

            if "json_path" in result:
                st.caption(f"📁 JSON Saved: {result['json_path']}")

            # -----------------------------
            # Confidence Score
            # -----------------------------
            if data.get("ocr_confidence") is not None:
                confidence = float(data["ocr_confidence"])
                st.progress(min(confidence, 1.0))
                st.caption(f"🔍 OCR Confidence: {round(confidence, 2)}")

            # -----------------------------
            # Extracted Data
            # -----------------------------
            st.subheader("📊 Extracted Data")

            col1, col2 = st.columns(2)

            with col1:
                st.info(f"🧾 Invoice No: {data.get('invoice_number') or 'Not found'}")
                st.info(f"📅 Date: {data.get('invoice_date') or 'Not found'}")
                st.info(f"👤 Customer: {data.get('customer_name') or 'Not found'}")

            with col2:
                st.info(f"📧 Email: {data.get('email') or 'Not found'}")
                st.info(f"📞 Phone: {data.get('phone_number') or 'Not found'}")
                st.success(f"💰 Total: ₹ {data.get('total_amount') or 'Not found'}")

            # -----------------------------
            # Line Items
            # -----------------------------
            if data.get("line_items"):
                st.subheader("🧾 Line Items")
                for item in data["line_items"]:
                    st.write(f"• {item}")

            # -----------------------------
            # Raw OCR Text (🔥 VERY IMPORTANT)
            # -----------------------------
            if data.get("raw_text"):
                with st.expander("🧾 View Raw OCR Text"):
                    st.text("\n".join(data["raw_text"]))

            # -----------------------------
            # Full JSON View
            # -----------------------------
            with st.expander("📦 Full JSON Output"):
                st.json(data)
