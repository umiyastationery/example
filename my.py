import os
import streamlit as st
from supabase import create_client, Client
from pdf2docx import Converter
import tempfile

# Supabase credentials
SUPABASE_URL = "https://exqbddsvjivjlzezdegm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4cWJkZHN2aml2amx6ZXpkZWdtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTA5MjkyMCwiZXhwIjoyMDU2NjY4OTIwfQ.5zecPjNfZBTa9n61fKL7LKbk4ntisY6wOHBkT96_pco"
BUCKET_NAME = "cloudbucket"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Streamlit UI
st.set_page_config(page_title="📂 File Converter & Storage", layout="wide")
st.title("📂 Upload & Convert Files with Supabase")

# File Upload Section
uploaded_file = st.file_uploader("Upload a file (PDF, Word)", type=["pdf", "docx"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
        temp_file.write(uploaded_file.read())
        temp_path = temp_file.name

    st.success(f"✅ File uploaded: {uploaded_file.name}")

    # Upload original file to Supabase
    try:
        with open(temp_path, "rb") as f:
            supabase.storage.from_(BUCKET_NAME).upload(f"original/{uploaded_file.name}", f)  # Removed 'upsert=True'
        st.success("✅ File stored in Supabase")

        # File Conversion Logic
        converted_file_path = None
        converted_file_name = None

        if uploaded_file.name.endswith(".pdf"):
            converted_file_name = uploaded_file.name.replace(".pdf", ".docx")
            converted_file_path = temp_path.replace(".pdf", ".docx")
            cv = Converter(temp_path)
            cv.convert(converted_file_path, start=0, end=None)
            cv.close()
        elif uploaded_file.name.endswith(".docx"):
            converted_file_name = uploaded_file.name.replace(".docx", ".pdf")
            converted_file_path = temp_path.replace(".docx", ".pdf")
            os.system(f"soffice --headless --convert-to pdf {temp_path}")  # Convert Word to PDF

        # Upload converted file to Supabase
        if converted_file_path:
            with open(converted_file_path, "rb") as f:
                supabase.storage.from_(BUCKET_NAME).upload(f"converted/{converted_file_name}", f)  # Removed 'upsert=True'

            st.success(f"✅ Converted File Saved: {converted_file_name}")

            # Download Link
            download_url = supabase.storage.from_(BUCKET_NAME).get_public_url(f"converted/{converted_file_name}")
            st.markdown(f"📥 *[Download Converted File]({download_url})*")

            # Cleanup temp files
            os.remove(temp_path)
            os.remove(converted_file_path)

    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")

st.write("🔒 *Your files are securely stored in Supabase!*")