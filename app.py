# app.py (نسخه نهایی با پشتیبانی کامل از فارسی)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

# --- کتابخانه‌های ضروری برای فارسی ---
import arabic_reshaper
from bidi.algorithm import get_display

from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- محاسبه مسیر مطلق فایل فونت (بدون تغییر) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "Vazirmatn-Regular.ttf")

def prepare_persian_text(text):
    """
    این تابع متن فارسی را برای نمایش صحیح در PDF آماده می‌کند.
    """
    reshaped_text = arabic_reshaper.reshape(text)  # 1. اتصال حروف
    bidi_text = get_display(reshaped_text)         # 2. اصلاح ترتیب نمایش (راست‌به‌چپ)
    return bidi_text

def create_pdf(text_content):
    print("--- Starting PDF creation with full Persian support ---")
    pdf = FPDF()
    pdf.add_page()
    
    try:
        print(f"Loading font from: {FONT_PATH}")
        if not os.path.exists(FONT_PATH):
            raise FileNotFoundError(f"Font file not found at path: {FONT_PATH}")

        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        pdf.set_font("Vazir", size=14)
        print("Font added and set successfully.")
        
        # <<< تغییر کلیدی: پردازش متن قبل از نوشتن >>>
        # متن ورودی را خط به خط جدا می‌کنیم
        lines = text_content.strip().split('\n')
        
        for i, line in enumerate(lines):
            if line.strip():
                # هر خط را برای نمایش صحیح فارسی آماده می‌کنیم
                processed_line = prepare_persian_text(line.strip())
                
                # برای راست‌چین کردن، از pdf.r_cell() یا تنظیم alignment استفاده می‌کنیم
                if i == 0: # خط اول را به عنوان تیتر و بزرگتر در نظر می‌گیریم
                    pdf.set_font("Vazir", size=18)
                    pdf.cell(0, 15, txt=processed_line, border=0, ln=1, align='C') # تیتر وسط‌چین
                    pdf.set_font("Vazir", size=14) # بازگشت به فونت معمولی
                else:
                    pdf.multi_cell(0, 10, txt=processed_line, border=0, align='R') # پاراگراف‌ها راست‌چین
        
        print("--- PDF content written successfully ---")

    except Exception:
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


# --- توابع دیگر (بدون تغییر) ---
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

# --- منطق اصلی (با حذف تبدیل به HTML) ---
def process_request(content, file_format):
    if file_format == 'pdf':
        # مستقیماً متن ساده را به تابع create_pdf ارسال می‌کنیم
        buffer = create_pdf(content)
        filename = 'export.pdf'
        mimetype = 'application/pdf'
    # بقیه فرمت‌ها بدون تغییر
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
