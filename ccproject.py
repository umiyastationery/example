import os
import streamlit as st
from supabase import create_client, Client
from pdf2docx import Converter
from PIL import Image
import tempfile
from streamlit_option_menu import option_menu

# Supabase Credentials
SUPABASE_URL = "https://exqbddsvjivjlzezdegm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4cWJkZHN2aml2amx6ZXpkZWdtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTA5MjkyMCwiZXhwIjoyMDU2NjY4OTIwfQ.5zecPjNfZBTa9n61fKL7LKbk4ntisY6wOHBkT96_pco"
BUCKET_NAME = "cloudbucket"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Streamlit UI Configuration
st.set_page_config(page_title="📂 File Converter & Storage", layout="wide")

# Sidebar Navigation
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Upload & Convert", "About"],
        icons=["house", "cloud-upload", "info-circle"],
        menu_icon="cast",
        default_index=1
    )

# Main App
st.title("📂 File Converter & Cloud Storage")

if selected == "Upload & Convert":
    uploaded_file = st.file_uploader("Upload a file (PDF, DOCX, JPG, PNG)", type=["pdf", "docx", "jpg", "png", "jpeg"])
    
    if uploaded_file:
        try:
            ext = os.path.splitext(uploaded_file.name)[1].lower()

            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_path = temp_file.name

            st.success(f"✅ File uploaded: {uploaded_file.name}")

            # Progress Bar
            progress = st.progress(0)
            progress.progress(30)

            # Upload original file to Supabase
            with open(temp_path, "rb") as f:
                supabase.storage.from_(BUCKET_NAME).upload(f"original/{uploaded_file.name}", f)
            
            progress.progress(60)
            st.success("✅ File stored in Supabase")

            # File Conversion Logic
            converted_file_path, converted_file_name = None, None

            if ext == ".pdf":
                converted_file_name = uploaded_file.name.replace(".pdf", ".docx")
                converted_file_path = temp_path.replace(".pdf", ".docx")
                cv = Converter(temp_path)
                cv.convert(converted_file_path, start=0, end=None)
                cv.close()

            elif ext == ".docx":
                converted_file_name = uploaded_file.name.replace(".docx", ".pdf")
                converted_file_path = temp_path.replace(".docx", ".pdf")

                # Alternative for Linux (docx2pdf does not work)
                try:
                    from docx2pdf import convert as docx_to_pdf
                    docx_to_pdf(temp_path, converted_file_path)
                except ImportError:
                    st.warning("⚠️ DOCX to PDF conversion requires Windows (MS Word).")

            elif ext in [".jpg", ".jpeg"]:
                converted_file_name = uploaded_file.name.replace(".jpg", ".png").replace(".jpeg", ".png")
                converted_file_path = temp_path.replace(".jpg", ".png").replace(".jpeg", ".png")
                img = Image.open(temp_path).convert("RGB")
                img.save(converted_file_path, "PNG")

            elif ext == ".png":
                converted_file_name = uploaded_file.name.replace(".png", ".jpg")
                converted_file_path = temp_path.replace(".png", ".jpg")
                img = Image.open(temp_path).convert("RGB")
                img.save(converted_file_path, "JPEG")

            elif ext in [".jpg", ".jpeg"]:
                converted_file_name = uploaded_file.name.replace(".jpg", ".pdf").replace(".jpeg", ".pdf")
                converted_file_path = temp_path.replace(".jpg", ".pdf").replace(".jpeg", ".pdf")
                img = Image.open(temp_path).convert("RGB")
                img.save(converted_file_path, "PDF")

            # Upload converted file to Supabase
            if converted_file_path:
                with open(converted_file_path, "rb") as f:
                    supabase.storage.from_(BUCKET_NAME).upload(f"converted/{converted_file_name}", f)

                progress.progress(100)
                st.success(f"✅ Converted File Saved: {converted_file_name}")

                # Download Link
                download_url = supabase.storage.from_(BUCKET_NAME).get_public_url(f"converted/{converted_file_name}")
                st.markdown(f"📥 [Download Converted File]({download_url})")

                # Cleanup temp files
                os.remove(temp_path)
                os.remove(converted_file_path)

        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

    st.write("🔒 Your files are securely stored in Supabase!")

elif selected == "Home":
    st.subheader("Welcome to the File Converter & Cloud Storage App!")
    st.markdown(
        """
        - ✅ Upload files securely to the cloud
        - 🔄 Convert between PDF, DOCX, PNG, and JPG
        - 📥 Download converted files instantly
        - 🔒 Safe & Secure with Supabase Cloud Storage
        """
    )
    st.image("https://www.supabase.io/images/supabase-logo-wordmark--dark.svg", width=300)

elif selected == "About":
    st.subheader("📌 About This App")
    st.markdown(
        """
        This app allows you to upload files, convert them to different formats, and store them securely in the cloud using **Supabase**.
        
        Developed using **Streamlit** and **Supabase API**, this app ensures:
        - Secure file storage
        - Fast and accurate file conversion
        - Easy-to-use interface
        
        🚀 Enjoy a hassle-free file conversion experience!
        """
    )
