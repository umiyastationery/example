import os
import streamlit as st
from supabase import create_client, Client
from pdf2docx import Converter
import tempfile
from PIL import Image
import img2pdf
from pdf2image import convert_from_path
import uuid
from datetime import datetime
from reportlab.pdfgen import canvas
import io

# Supabase credentials
SUPABASE_URL = "https://exqbddsvjivjlzezdegm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4cWJkZHN2aml2amx6ZXpkZWdtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTA5MjkyMCwiZXhwIjoyMDU2NjY4OTIwfQ.5zecPjNfZBTa9n61fKL7LKbk4ntisY6wOHBkT96_pco"
BUCKET_NAME = "cloudbucket"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_unique_filename(filename):
    """Generate a unique filename by adding timestamp and UUID."""
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{name}_{timestamp}_{unique_id}{ext}"

def convert_image_format(input_path, output_path):
    """Convert between image formats (JPG/PNG)."""
    img = Image.open(input_path)
    if output_path.lower().endswith('.png'):
        img = img.convert('RGBA')
    else:
        img = img.convert('RGB')
    img.save(output_path)

def image_to_pdf(input_path, output_path):
    """Convert image to PDF."""
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(input_path))

def text_to_pdf(input_path, output_path):
    """Convert text file to PDF."""
    c = canvas.Canvas(output_path)
    with open(input_path, 'r', encoding='utf-8') as file:
        y = 800
        for line in file:
            if y < 50:
                c.showPage()
                y = 800
            c.drawString(50, y, line.strip())
            y -= 15
    c.save()

def pdf_to_images(input_path, output_dir):
    """Convert PDF to images."""
    pages = convert_from_path(input_path)
    image_paths = []
    for i, page in enumerate(pages):
        image_path = os.path.join(output_dir, f'page_{i+1}.png')
        page.save(image_path, 'PNG')
        image_paths.append(image_path)
    return image_paths

def docx_to_pdf(input_path, output_path):
    """Convert Word document to PDF using python-docx and reportlab."""
    from docx import Document
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    # Read the Word document
    doc = Document(input_path)
    pdf = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    y = height - 50  # Start from top of page
    
    for para in doc.paragraphs:
        if y < 50:  # Check if we need a new page
            pdf.showPage()
            y = height - 50
        
        # Handle different paragraph styles
        if para.style.name.startswith('Heading'):
            pdf.setFont("Helvetica-Bold", 14)
        else:
            pdf.setFont("Helvetica", 12)
        
        # Write the text
        text = para.text.strip()
        if text:
            pdf.drawString(50, y, text)
            y -= 20  # Move down for next line
    
    pdf.save()

# Streamlit UI
st.set_page_config(
    page_title="🔄 Universal File Converter",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1e7dd;
        color: #0f5132;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🛠️ Conversion Options")
    conversion_type = st.selectbox(
        "Select Conversion Type",
        [
            "PDF to Word (.pdf → .docx)",
            "Word to PDF (.docx → .pdf)",
            "Image to PDF (.jpg/.png → .pdf)",
            "PDF to Image (.pdf → .jpg/.png)",
            "Text to PDF (.txt → .pdf)",
            "JPG to PNG (.jpg → .png)",
            "PNG to JPG (.png → .jpg)"
        ]
    )

# Main content
st.title("🔄 Universal File Converter")
st.markdown("### Upload your file for conversion")

# Determine accepted file types based on conversion type
accepted_types = {
    "PDF to Word (.pdf → .docx)": ["pdf"],
    "Word to PDF (.docx → .pdf)": ["docx"],
    "Image to PDF (.jpg/.png → .pdf)": ["jpg", "jpeg", "png"],
    "PDF to Image (.pdf → .jpg/.png)": ["pdf"],
    "Text to PDF (.txt → .pdf)": ["txt"],
    "JPG to PNG (.jpg → .png)": ["jpg", "jpeg"],
    "PNG to JPG (.png → .jpg)": ["png"]
}

uploaded_file = st.file_uploader(
    "Choose a file",
    type=accepted_types[conversion_type],
    help="Select the file you want to convert"
)

if uploaded_file:
    try:
        # Create unique filename
        unique_filename = generate_unique_filename(uploaded_file.name)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded file
            input_path = os.path.join(temp_dir, unique_filename)
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Determine output filename and conversion logic
            if conversion_type == "PDF to Word (.pdf → .docx)":
                output_filename = unique_filename.replace(".pdf", ".docx")
                output_path = os.path.join(temp_dir, output_filename)
                cv = Converter(input_path)
                cv.convert(output_path)
                cv.close()

            elif conversion_type == "Word to PDF (.docx → .pdf)":
                output_filename = unique_filename.replace(".docx", ".pdf")
                output_path = os.path.join(temp_dir, output_filename)
                docx_to_pdf(input_path, output_path)

            elif conversion_type == "Image to PDF (.jpg/.png → .pdf)":
                output_filename = os.path.splitext(unique_filename)[0] + ".pdf"
                output_path = os.path.join(temp_dir, output_filename)
                image_to_pdf(input_path, output_path)

            elif conversion_type == "PDF to Image (.pdf → .jpg/.png)":
                image_paths = pdf_to_images(input_path, temp_dir)
                for img_path in image_paths:
                    with open(img_path, "rb") as f:
                        img_filename = os.path.basename(img_path)
                        supabase.storage.from_(BUCKET_NAME).upload(
                            f"converted/{img_filename}",
                            f
                        )

            elif conversion_type == "Text to PDF (.txt → .pdf)":
                output_filename = unique_filename.replace(".txt", ".pdf")
                output_path = os.path.join(temp_dir, output_filename)
                text_to_pdf(input_path, output_path)

            elif conversion_type in ["JPG to PNG (.jpg → .png)", "PNG to JPG (.png → .jpg)"]:
                output_ext = ".png" if conversion_type.startswith("JPG") else ".jpg"
                output_filename = os.path.splitext(unique_filename)[0] + output_ext
                output_path = os.path.join(temp_dir, output_filename)
                convert_image_format(input_path, output_path)

            # Upload original file
            with open(input_path, "rb") as f:
                supabase.storage.from_(BUCKET_NAME).upload(
                    f"original/{unique_filename}",
                    f
                )

            # Upload converted file(s)
            if conversion_type != "PDF to Image (.pdf → .jpg/.png)":
                with open(output_path, "rb") as f:
                    supabase.storage.from_(BUCKET_NAME).upload(
                        f"converted/{output_filename}",
                        f
                    )
                
                # Generate download link
                download_url = supabase.storage.from_(BUCKET_NAME).get_public_url(f"converted/{output_filename}")
                
                # Success message with download link
                st.success("✅ Conversion completed successfully!")
                st.markdown(f"📥 **[Download Converted File]({download_url})**")
            else:
                st.success("✅ PDF pages converted to images successfully!")
                st.markdown("### Generated Images:")
                for i, _ in enumerate(image_paths):
                    img_filename = f"page_{i+1}.png"
                    img_url = supabase.storage.from_(BUCKET_NAME).get_public_url(f"converted/{img_filename}")
                    st.markdown(f"📥 **[Download Page {i+1}]({img_url})**")

    except Exception as e:
        st.error(f"⚠️ Error during conversion: {str(e)}")
        st.error("Please try again or contact support if the issue persists.")

# Footer
st.markdown("---")
st.markdown("🔒 *Your files are securely stored and processed*")
st.markdown("💡 *Tip: All converted files are given unique names to prevent conflicts*")
