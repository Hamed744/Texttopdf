import os
import io
from flask import Flask, request, jsonify, send_file, render_template

# Import new library for PDF and other libraries
from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- Final and Robust Font Loading ---
FONT_FILE_NAME = 'Vazirmatn-Regular.ttf'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, FONT_FILE_NAME)

# --- PDF Generation with fpdf2 ---
def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    
    # Check if font exists and add it
    if os.path.exists(FONT_PATH):
        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        pdf.set_font('Vazir', '', 12)
    else:
        # Fallback to a default font if Vazir is not found
        pdf.set_font('Arial', '', 12)
        # Add a warning to the PDF itself
        pdf.cell(0, 10, 'WARNING: Persian font not found. Text may not render correctly.', 0, 1, 'C')

    # Set text direction to Right-to-Left
    pdf.set_right_to_left(True)
    
    # Use multi_cell to automatically handle line breaks
    pdf.multi_cell(0, 10, text_content)
    
    # Generate the PDF in memory
    pdf_output = pdf.output(dest='S').encode('latin-1')
    buffer = io.BytesIO(pdf_output)
    buffer.seek(0)
    return buffer

# --- Other file generation functions (no changes needed) ---
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

# --- Main request processing logic (no changes needed) ---
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

# --- Flask routes (no changes needed) ---
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
            return "Internal Server Error", 500
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
