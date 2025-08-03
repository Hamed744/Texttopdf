import os
import io
import base64
from flask import Flask, request, jsonify, send_file, render_template

# Import necessary libraries
from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- PASTE YOUR BASE64 FONT STRING HERE ---
# Replace the placeholder text inside the triple quotes with your copied Base64 string
VAZIR_FONT_BASE64 = """
 paste_your_very_long_base64_string_here 
"""
# ---

# --- PDF Generation with Embedded Font (No File System Access) ---
def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    
    try:
        # Decode the Base64 font data
        font_data = base64.b64decode(VAZIR_FONT_BASE64)
        
        # fpdf2 can load font from byte data directly, which is perfect for this.
        # We give it a "name" so it knows what type of file it is.
        pdf.add_font('Vazir', '', io.BytesIO(font_data), uni=True)
        pdf.set_font('Vazir', '', 12)
        pdf.set_right_to_left(True)
    except Exception as e:
        # If anything goes wrong, fall back to default font
        print(f"Font embedding failed: {e}. Falling back to Arial.")
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, 'WARNING: Persian font could not be embedded.', 0, 1, 'C')

    pdf.multi_cell(0, 10, text_content)
    
    pdf_output = pdf.output(dest='S').encode('latin-1')
    buffer = io.BytesIO(pdf_output)
    buffer.seek(0)
    return buffer

# --- Other file generation functions (no changes) ---
def create_docx(text_content):
    buffer = io.BytesIO()
    document = Document()
    p = document.add_paragraph(text_content)
    p.alignment = 3
    document.save(buffer)
    buffer.seek(0)
    return buffer

def create_txt(text_content):
    buffer = io.BytesIO(text_content.encode('utf-8'))
    buffer.seek(0)
    return buffer
    
def create_xlsx(text_content):
    buffer = io.BytesIO()
    workbook = Workbook()
    sheet = workbook.active
    sheet.sheet_view.rightToLeft = True
    for i, line in enumerate(text_content.split('\n'), 1):
         sheet[f'A{i}'] = line
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

# --- Main request processing logic (no changes) ---
def process_request(content, file_format):
    if file_format == 'pdf':
        buffer = create_pdf(content)
        filename = 'export.pdf'
        mimetype = 'application/pdf'
    elif file_format == 'docx':
        buffer = create_docx(content)
        filename = 'export.docx'
        mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif file_format == 'xlsx':
        buffer = create_xlsx(content)
        filename = 'export.xlsx'
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        buffer = create_txt(content)
        filename = 'export.txt'
        mimetype = 'text/plain'

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )

# --- Flask routes (no changes) ---
@app.route('/convert', methods=['POST'])
def convert_text_api():
    try:
        data = request.json
        content = data.get('content')
        file_format = data.get('format', 'txt').lower()
        if not content:
            return jsonify({"error": "No content provided"}), 400
        return process_request(content, file_format)
    except Exception as e:
        print(f"🔥🔥🔥 API Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            content = request.form.get('content')
            file_format = request.form.get('format', 'txt').lower()
            if not content:
                return "لطفا متنی برای تبدیل وارد کنید.", 400
            return process_request(content, file_format)
        except Exception as e:
            print(f"🔥🔥🔥 Web Form Error: {e}")
            return "An internal server error occurred while processing your request.", 500
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
