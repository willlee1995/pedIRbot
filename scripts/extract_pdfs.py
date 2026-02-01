"""
Extract text from HKCH appointment PDFs using PyMuPDF -> PNG -> Tesseract OCR
Always use image-based OCR for better Chinese character recognition
"""
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os

# Set Tesseract executable path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

pdf_dir = r"d:\Development area\pedIRbot\KB\HKCH Appt sheet"
output_dir = os.path.join(pdf_dir, "extracted")
os.makedirs(output_dir, exist_ok=True)

pdf_files = ["vir.pdf", "nvir.pdf", "usir.pdf", "li.pdf"]

for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_dir, pdf_file)
    if not os.path.exists(pdf_path):
        print(f"Skipping {pdf_file} - not found")
        continue

    print(f"\n=== Processing {pdf_file} ===")

    try:
        doc = fitz.open(pdf_path)
        print(f"Opened PDF with {len(doc)} pages")

        full_text = ""
        for page_num, page in enumerate(doc):
            print(f"  Converting page {page_num + 1} to image...")

            # Always render page to high-res image for OCR
            mat = fitz.Matrix(3, 3)  # 3x zoom for better OCR quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Save the image for reference
            img_dir = os.path.join(output_dir, "images")
            os.makedirs(img_dir, exist_ok=True)
            img_path = os.path.join(img_dir, f"{pdf_file.replace('.pdf', '')}_page_{page_num + 1}.png")
            img.save(img_path)
            print(f"    Saved image: {img_path}")

            # OCR with Traditional Chinese + English
            print(f"  Running OCR on page {page_num + 1}...")
            text = pytesseract.image_to_string(img, lang='chi_tra+eng')
            full_text += f"\n--- Page {page_num + 1} ---\n{text}\n"

        doc.close()

        # Save to markdown
        output_file = os.path.join(output_dir, pdf_file.replace(".pdf", ".md"))
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {pdf_file.replace('.pdf', '').upper()} Appointment Sheet\n\n")
            f.write(full_text)

        print(f"Saved to {output_file}")

    except Exception as e:
        print(f"Error processing {pdf_file}: {e}")
        import traceback
        traceback.print_exc()

print("\nDone!")
