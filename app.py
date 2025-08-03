import os
import io
from flask import Flask, request, jsonify, send_file, render_template

# Import libraries for file generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- PDF Generation with Persian Support ---
FONT_NAME = 'Vazir'
FONT_FILE = 'Vazirmatn-Regular.ttf'

try:
    if os.path.exists(FONT_FILE):
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
        print(f"✅ فونت '{FONT_NAME}' با موفقیت بارگذاری شد.")
    else:
        print(f"⚠️ هشدار: فایل فونت '{FONT_FILE}' یافت نشد. PDF فارسی ممکن است به درستی نمایش داده نشود.")
        FONT_NAME = 'Helvetica' # Fallback font
except Exception as e:
    print(f"خطا در بارگذاری فونت: {e}")
    FONT_NAME = 'Helvetica' # Fallback font


def create_pdf(text_content):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont(FONT_NAME, 12)
    
    # Set text direction to Right-to-Left
    p.setRTL()
    
    text_object = p.beginText()
    text_object.setTextOrigin(letter[0] - 100, letter[1] - 100) # Start from top-right
    text_object.setFont(FONT_NAME, 12)
    
    lines = text_content.split('\n')
    for line in lines:
        text_object.textLine(line)
        
    p.drawText(text_object)
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- Word (.docx) Generation ---
def create_docx(text_content):
    buffer = io.BytesIO()
    document = Document()
    # Add paragraph with right-to-left direction
    p = document.add_paragraph(text_content)
    p.alignment = 3 # 3 is for right alignment in python-docx
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
    sheet.sheet_view.rightToLeft = True # Set sheet direction to RTL
    
    # Split content by lines and put in different rows
    for i, line in enumerate(text_content.split('\n'), 1):
         sheet[f'A{i}'] = line
         
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

# API Endpoint for your chatbot
@app.route('/convert', methods=['POST'])
def convert_text_api():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
        
    content = data.get('content')
    file_format = data.get('format', 'txt').lower()

    if not content:
        return jsonify({"error": "No content provided"}), 400

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
    else: # Default to txt
        buffer = create_txt(content)
        filename = 'export.txt'
        mimetype = 'text/plain'

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )

# Web page for manual conversion
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        file_format = request.form.get('format', 'txt').lower()
        
        if not content:
            return "لطفا متنی برای تبدیل وارد کنید.", 400
        
        # Reuse the same logic as the API
        return convert_text_api.__wrapped__(request)

    return render_template('index.html')

if __name__ == '__main__':
    # For local development
    app.run(debug=True)
