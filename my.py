import os
import streamlit as st
from supabase import create_client, Client
from pdf2docx import Converter
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import uuid
from datetime import datetime

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
uploaded_file = st.file_uploader("Upload a file (PDF, Word, Image)", type=["pdf", "docx", "jpg", "jpeg", "png"])

if uploaded_file:
    # Generate a unique file name to avoid conflicts
    file_name, file_extension = os.path.splitext(uploaded_file.name)
    unique_id = uuid.uuid4().hex
    unique_file_name = f"{file_name}_{unique_id}{file_extension}"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(uploaded_file.read())
        temp_path = temp_file.name

    st.success(f"✅ File uploaded: {uploaded_file.name}")

    # Upload original file to Supabase
    try:
        with open(temp_path, "rb") as f:
            supabase.storage.from_(BUCKET_NAME).upload(f"original/{unique_file_name}", f)
        st.success("✅ File stored in Supabase")

        # File Conversion Logic
        converted_file_path = None
        converted_file_name = None

        if uploaded_file.name.endswith(".pdf"):
            # PDF to Word
            converted_file_name = unique_file_name.replace(".pdf", ".docx")
            converted_file_path = temp_path.replace(".pdf", ".docx")
            cv = Converter(temp_path)
            cv.convert(converted_file_path, start=0, end=None)
            cv.close()
        elif uploaded_file.name.endswith(".docx"):
            # Word to PDF
            converted_file_name = unique_file_name.replace(".docx", ".pdf")
            converted_file_path = temp_path.replace(".docx", ".pdf")
            os.system(f"soffice --headless --convert-to pdf {temp_path}")
        elif uploaded_file.name.lower().endswith((".jpg", ".jpeg", ".png")):
            # Image to PDF
            converted_file_name = unique_file_name.replace(file_extension, ".pdf")
            converted_file_path = temp_path.replace(file_extension, ".pdf")
            image = Image.open(temp_path)
            image.save(converted_file_path, "PDF", resolution=100.0)
        elif uploaded_file.name.endswith(".pdf"):
            # PDF to Image (JPG)
            converted_file_name = unique_file_name.replace(".pdf", ".jpg")
            converted_file_path = temp_path.replace(".pdf", ".jpg")
            images = convert_from_path(temp_path)
            images[0].save(converted_file_path, "JPEG")
        elif uploaded_file.name.lower().endswith(".jpg"):
            # JPG to PNG
            converted_file_name = unique_file_name.replace(".jpg", ".png")
            converted_file_path = temp_path.replace(".jpg", ".png")
            image = Image.open(temp_path)
            image.save(converted_file_path, "PNG")
        elif uploaded_file.name.lower().endswith(".png"):
            # PNG to JPG
            converted_file_name = unique_file_name.replace(".png", ".jpg")
            converted_file_path = temp_path.replace(".png", ".jpg")
            image = Image.open(temp_path)
            image.save(converted_file_path, "JPEG")

        # Upload converted file to Supabase
        if converted_file_path:
            with open(converted_file_path, "rb") as f:
                supabase.storage.from_(BUCKET_NAME).upload(f"converted/{converted_file_name}", f)

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
