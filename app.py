# app.py (نسخه نهایی با مدیریت صحیح صفحات طولانی)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

# --- کتابخانه‌های ضروری برای فارسی (بدون تغییر) ---
import arabic_reshaper
from bidi.algorithm import get_display

from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- مسیر فونت (بدون تغییر) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "Vazirmatn-Regular.ttf")

def prepare_persian_text(text):
    """
    تابع آماده‌سازی متن فارسی (بدون تغییر)
    """
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def create_pdf(text_content):
    """
    تابع ساخت PDF بازنویسی شده برای پشتیبانی از متن‌های چند صفحه‌ای
    """
    print("--- Starting PDF creation with improved page-break handling ---")
    pdf = FPDF()
    pdf.add_page()
    
    try:
        # --- بخش تنظیم فونت (بدون تغییر) ---
        print(f"Loading font from: {FONT_PATH}")
        if not os.path.exists(FONT_PATH):
            raise FileNotFoundError(f"Font file not found at path: {FONT_PATH}")
        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        print("Font added successfully.")

        # <<< تغییر کلیدی: پردازش متن به صورت یکپارچه >>>

        # 1. جدا کردن تیتر از بدنه اصلی متن
        lines = text_content.strip().split('\n')
        title = lines[0].strip() if lines else ""
        # تمام خطوط بعدی را به هم متصل می‌کنیم تا یک بدنه یکپارچه داشته باشیم
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        # 2. پردازش و نوشتن تیتر (اگر وجود داشته باشد)
        if title:
            pdf.set_font("Vazir", size=18)
            processed_title = prepare_persian_text(title)
            pdf.cell(0, 15, txt=processed_title, border=0, ln=1, align='C')
            pdf.ln(5) # ایجاد کمی فاصله بعد از تیتر

        # 3. پردازش کل بدنه متن و نوشتن آن با یک دستور multi_cell
        if body:
            pdf.set_font("Vazir", size=12)
            processed_body = prepare_persian_text(body)
            # این روش به fpdf2 اجازه می‌دهد خودش صفحات را مدیریت کند
            pdf.multi_cell(0, 10, txt=processed_body, border=0, align='R')

        print("--- PDF content written successfully ---")

    except Exception:
        # بلوک مدیریت خطا (بدون تغییر)
        print("🔥🔥🔥 PDF CREATION FAILED! See traceback below. 🔥🔥🔥")
        print(traceback.format_exc())
        
        if not pdf.page_no():
            pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ERROR: Could not generate PDF. Please check server logs.', 0, 1, 'C')

    print("Generating PDF output bytes...")
    pdf_output = pdf.output()
    buffer = io.BytesIO(pdf_output)
    buffer.seek(0)
    print("--- PDF creation finished ---")
    return buffer


# --- بقیه فایل app.py (توابع دیگر و روت‌ها) بدون هیچ تغییری باقی می‌ماند ---

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

if __name__ == '__main__':
    app.run(debug=True)
