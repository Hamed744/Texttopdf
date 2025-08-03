import os
import io
from flask import Flask, request, jsonify, send_file, render_template

# Import necessary libraries
from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- Get the absolute path to the directory where this script is located ---
# This ensures that files are found correctly on any server.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- PDF Generation with fpdf2 (More reliable) ---
def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    
    font_path = os.path.join(BASE_DIR, 'Vazirmatn-Regular.ttf')
    
    # Check if the font file exists at the specified absolute path
    if os.path.exists(font_path):
        # Add the Persian font. uni=True is crucial for Unicode support.
        pdf.add_font('Vazir', '', font_path, uni=True)
        pdf.set_font('Vazir', '', 12)
        # Set text direction to Right-to-Left
        pdf.set_right_to_left(True)
    else:
        # Fallback to a default font if Vazirmatn is not found
        # This prevents the app from crashing.
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, 'WARNING: Persian font (Vazirmatn-Regular.ttf) not found in the project directory.', 0, 1, 'C')

    # Use multi_cell to automatically handle line breaks and write the text
    pdf.multi_cell(0, 10, text_content)
    
    # Generate the PDF in memory
    pdf_output = pdf.output(dest='S').encode('latin-1')
    buffer = io.BytesIO(pdf_output)
    buffer.seek(0)
    return buffer

# --- Word (.docx) Generation ---
def create_docx(text_content):
    buffer = io.BytesIO()
    document = Document()
    p = document.add_paragraph(text_content)
    p.alignment = 3  # 3 corresponds to WD_ALIGN_PARAGRAPH.RIGHT
    document.save(buffer)
    buffer.seek(0)
    return buffer

# --- Plain Text (.txt) Generation ---
def create_txt(text_content):
    buffer = io.BytesIO(text_content.encode('utf-8'))
    buffer.seek(0)
    return buffer

# --- Excel (.xlsx) Generation ---
def create_xlsx(text_content):
    buffer = io.BytesIO()
    workbook = Workbook()
    sheet = workbook.active
    sheet.sheet_view.rightToLeft = True
    # Split content by lines and put each line in a new row
    for i, line in enumerate(text_content.split('\n'), 1):
         sheet[f'A{i}'] = line
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

# --- Main logic to process the request and send the file ---
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
    else: # Default to .txt
        buffer = create_txt(content)
        filename = 'export.txt'
        mimetype = 'text/plain'

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )

# --- API Endpoint for your chatbot ---
@app.route('/convert', methods=['POST'])
def convert_text_api():
    try:
        data = request.json
        if not data: return jsonify({"error": "Invalid JSON"}), 400
        content = data.get('content')
        file_format = data.get('format', 'txt').lower()
        if not content:
            return jsonify({"error": "No content provided"}), 400
        return process_request(content, file_format)
    except Exception as e:
        print(f"🔥🔥🔥 API Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# --- Web Page for manual conversion ---
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
            # This is important for debugging!
            print(f"🔥🔥🔥 Web Form Error: {e}")
            return "An internal server error occurred while processing your request.", 500
    return render_template('index.html')


if __name__ == '__main__':
    # This block is for local development
    app.run(debug=True)
