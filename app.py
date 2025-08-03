# app.py (نسخه نهایی با مسیر مطلق و وابستگی fonttools)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

# Import necessary libraries
from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- محاسبه مسیر مطلق فایل فونت ---
# این کد مسیر پوشه‌ای که app.py در آن قرار دارد را پیدا می‌کند
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# و نام فایل فونت را به آن اضافه می‌کند تا یک مسیر کامل و دقیق بسازد
FONT_PATH = os.path.join(BASE_DIR, "Vazirmatn-Regular.ttf")

# --- ساخت PDF با خواندن مستقیم فایل فونت از مسیر مطلق ---
def create_pdf(text_content):
    print("--- Starting PDF creation with ABSOLUTE PATH method ---")
    pdf = FPDF()
    pdf.add_page()
    
    try:
        print(f"Attempting to load font from absolute path: {FONT_PATH}")
        # بررسی می‌کنیم آیا فایل واقعاً در این مسیر وجود دارد یا نه
        if not os.path.exists(FONT_PATH):
            # اگر فایل پیدا نشود، یک خطای واضح و مشخص در لاگ چاپ می‌شود
            raise FileNotFoundError(f"CRITICAL: Font file not found at path: {FONT_PATH}")

        print("Font file found! Adding to FPDF...")
        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        
        print("Setting PDF font to Vazir...")
        pdf.set_font('Vazir', '', 12)
        pdf.set_right_to_left(True)
        print("--- Font embedding successful ---")

    except Exception:
        print("🔥🔥🔥 FONT EMBEDDING FAILED! See traceback below. 🔥🔥🔥")
        # چاپ کامل خطا در لاگ برای دیباگ نهایی
        print(traceback.format_exc())
        
        print("Falling back to default Arial font.")
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'WARNING: Persian font could not be loaded. Check server logs.', 0, 1, 'C')
        pdf.set_font('Arial', '', 12)

    print("Writing text content to PDF...")
    pdf.multi_cell(0, 10, text_content)
    
    print("Generating PDF output bytes...")
    pdf_output = pdf.output()
    buffer = io.BytesIO(pdf_output)
    buffer.seek(0)
    print("--- PDF creation finished ---")
    return buffer

# --- سایر توابع بدون تغییر ---
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

# --- منطق اصلی و روت‌ها (بدون تغییر) ---
def process_request(content, file_format):
    try:
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
    except Exception:
        print(f"🔥🔥🔥 An uncaught error occurred in process_request for format '{file_format}' 🔥🔥🔥")
        print(traceback.format_exc())
        return "An internal server error occurred while generating the file.", 500

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        file_format = request.form.get('format', 'txt').lower()
        if not content:
            return "لطفا متنی برای تبدیل وارد کنید.", 400
        return process_request(content, file_format)
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True)
