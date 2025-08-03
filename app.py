# app.py (نسخه نهایی با تبدیل خودکار متن به HTML زیبا)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

# Import necessary libraries
from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- محاسبه مسیر مطلق فایل فونت (همچنان ضروری است) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "Vazirmatn-Regular.ttf")

def beautify_text_to_html(plain_text):
    """
    این تابع متن ساده را می‌گیرد و آن را در یک قالب HTML زیبا قرار می‌دهد.
    خط اول به عنوان تیتر و بقیه خطوط به عنوان پاراگراف در نظر گرفته می‌شوند.
    """
    # جدا کردن خطوط متن
    lines = plain_text.strip().split('\n')
    
    # استایل‌دهی (CSS) برای زیبایی صفحه
    html_style = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');
        body {
            font-family: 'Vazirmatn', sans-serif;
            direction: rtl;
            line-height: 1.8;
            font-size: 12pt;
            color: #333;
            width: 100%;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }
        h1 {
            color: #1095c1;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        p {
            text-align: justify;
            margin-bottom: 12px;
        }
    </style>
    """
    
    # ساخت بدنه HTML
    html_body = ""
    if lines:
        # خط اول به عنوان تیتر H1
        html_body += f"<h1>{lines[0]}</h1>"
        # بقیه خطوط به عنوان پاراگراف
        for line in lines[1:]:
            if line.strip(): # فقط خطوط غیرخالی را اضافه کن
                html_body += f"<p>{line}</p>"

    # ترکیب نهایی و ساخت یک صفحه کامل HTML
    full_html = f'<!DOCTYPE html><html><head><meta charset="UTF-8">{html_style}</head><body>{html_body}</body></html>'
    return full_html

# --- ساخت PDF با رندر HTML (این تابع دیگر تغییر نمی‌کند) ---
def create_pdf(html_content):
    print("--- Starting PDF creation from auto-generated HTML ---")
    pdf = FPDF()
    pdf.add_page()
    
    try:
        print(f"Loading font from: {FONT_PATH}")
        if not os.path.exists(FONT_PATH):
            raise FileNotFoundError(f"Font file not found at path: {FONT_PATH}")

        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        print("Font added successfully.")
        
        print("Rendering HTML content...")
        pdf.write_html(html_content)
        
        print("--- HTML rendering successful ---")

    except Exception:
        print("🔥🔥🔥 PDF CREATION FAILED! See traceback below. 🔥🔥🔥")
        print(traceback.format_exc())
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ERROR: Could not generate PDF. Please check server logs.', 0, 1, 'C')

    print("Generating PDF output bytes...")
    pdf_output = pdf.output()
    buffer = io.BytesIO(pdf_output)
    buffer.seek(0)
    print("--- PDF creation finished ---")
    return buffer

# --- توابع DOCX, TXT, XLSX (بدون تغییر) ---
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

# --- منطق اصلی پردازش درخواست (با تغییر کوچک برای PDF) ---
def process_request(content, file_format):
    if file_format == 'pdf':
        # مرحله ۱: تبدیل متن ساده به HTML زیبا
        html_output = beautify_text_to_html(content)
        # مرحله ۲: ساخت PDF از روی HTML
        buffer = create_pdf(html_output)
        filename = 'export.pdf'
        mimetype = 'application/pdf'
    elif file_format == 'docx':
        buffer = create_docx(content)
        filename = 'export.docx'
        mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    # ... بقیه فرمت‌ها بدون تغییر
    elif file_format == 'xlsx':
        buffer = create_xlsx(content)
        filename = 'export.xlsx'
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        buffer = create_txt(content)
        filename = 'export.txt'
        mimetype = 'text/plain'
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)

# --- روت‌ها (بدون تغییر) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        file_format = request.form.get('format', 'txt').lower()
        if not content:
            return "لطفا متنی برای تبدیل وارد کنید.", 400
        return process_request(content, file_format)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
