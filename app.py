# app.py (نسخه نهایی با قابلیت رندر HTML)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

# Import necessary libraries
from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- محاسبه مسیر مطلق فایل فونت (بدون تغییر) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "Vazirmatn-Regular.ttf")

# --- ساخت PDF با رندر مستقیم HTML ---
def create_pdf(html_content):
    print("--- Starting PDF creation using HTML rendering method ---")
    pdf = FPDF()
    pdf.add_page()
    
    try:
        print(f"Loading font from: {FONT_PATH}")
        if not os.path.exists(FONT_PATH):
            raise FileNotFoundError(f"Font file not found at path: {FONT_PATH}")

        # فونت را اضافه می‌کنیم تا در HTML قابل استفاده باشد
        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        print("Font added successfully.")

        # <<< تغییر کلیدی: استفاده از write_html >>>
        # این تابع به صورت هوشمند متن را بر اساس تگ‌های HTML می‌چیند
        # و از آنجایی که فونت ما فارسی است، راست‌چین را به درستی مدیریت می‌کند.
        print("Rendering HTML content...")
        pdf.write_html(f'<div dir="rtl" style="font-family: Vazir; font-size: 12pt;">{html_content}</div>')
        
        print("--- HTML rendering successful ---")

    except Exception:
        print("🔥🔥🔥 PDF CREATION FAILED! See traceback below. 🔥🔥🔥")
        print(traceback.format_exc())
        # اگر خطا رخ دهد، یک صفحه PDF با پیام خطا ایجاد می‌کنیم
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ERROR: Could not generate PDF. Please check server logs.', 0, 1, 'C')

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
    if file_format == 'pdf':
        buffer = create_pdf(content) # این تابع حالا محتوای HTML می‌گیرد
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
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)

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
