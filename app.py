# app.py (نسخه نهایی با قابلیت افزودن پاورقی در تمام فایل‌ها)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

# --- کتابخانه‌های ضروری برای فارسی ---
import arabic_reshaper
from bidi.algorithm import get_display

from fpdf import FPDF
from docx import Document
# برای استایل‌دهی در اکسل
from openpyxl import Workbook
from openpyxl.styles import Alignment

app = Flask(__name__)

# --- مسیر فونت و متن پاورقی ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "Vazirmatn-Regular.ttf")
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"

def prepare_persian_text(text):
    """تابع آماده‌سازی متن فارسی (بدون تغییر)"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def create_pdf(text_content):
    """ساخت PDF با افزودن پاورقی در انتهای آخرین صفحه"""
    print("--- Starting PDF creation with footer ---")
    pdf = FPDF()
    pdf.add_page()
    
    try:
        # --- بخش تنظیم فونت و نوشتن متن اصلی (بدون تغییر) ---
        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        
        lines = text_content.strip().split('\n')
        title = lines[0].strip() if lines else ""
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        if title:
            pdf.set_font("Vazir", size=18)
            processed_title = prepare_persian_text(title)
            pdf.cell(0, 15, txt=processed_title, border=0, ln=1, align='C')
            pdf.ln(5)

        if body:
            pdf.set_font("Vazir", size=12)
            processed_body = prepare_persian_text(body)
            pdf.multi_cell(0, 10, txt=processed_body, border=0, align='R')
        
        # <<< تغییر کلیدی: افزودن پاورقی در انتهای PDF >>>
        # مکان‌نما را به 3 سانتی‌متری پایین صفحه منتقل می‌کنیم
        pdf.set_y(-30)
        pdf.set_font("Vazir", size=10)
        # رنگ متن را آبی می‌کنیم (RGB: 0, 123, 255)
        pdf.set_text_color(0, 123, 255)
        processed_footer = prepare_persian_text(FOOTER_TEXT)
        # پاورقی را به صورت وسط‌چین چاپ می‌کنیم
        pdf.cell(0, 10, txt=processed_footer, border=0, ln=1, align='C')
        
        print("--- Footer added to PDF successfully ---")

    except Exception:
        # ... بلوک خطا ...
        print("🔥🔥🔥 PDF CREATION FAILED! See traceback below. 🔥🔥🔥")
        print(traceback.format_exc())
        if not pdf.page_no(): pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ERROR: Could not generate PDF. Please check server logs.', 0, 1, 'C')

    pdf_output = pdf.output()
    return io.BytesIO(pdf_output)

def create_docx(text_content):
    """ساخت DOCX با افزودن پاورقی استاندارد"""
    document = Document()
    p = document.add_paragraph(text_content)
    p.alignment = 3
    
    # <<< تغییر کلیدی: افزودن پاورقی به فایل ورد >>>
    footer = document.sections[0].footer
    footer_p = footer.paragraphs[0]
    footer_p.text = FOOTER_TEXT
    # 1 یعنی وسط‌چین (WD_ALIGN_PARAGRAPH.CENTER)
    footer_p.alignment = 1

    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

def create_txt(text_content):
    """ساخت TXT با افزودن متن در انتها"""
    # <<< تغییر کلیدی: افزودن پاورقی به فایل متنی >>>
    full_content = f"{text_content}\n\n\n---\n{FOOTER_TEXT}"
    return io.BytesIO(full_content.encode('utf-8'))
    
def create_xlsx(text_content):
    """ساخت XLSX با افزودن پاورقی در ردیف‌های پایینی"""
    workbook = Workbook()
    sheet = workbook.active
    sheet.sheet_view.rightToLeft = True
    
    for i, line in enumerate(text_content.split('\n'), 1):
         sheet[f'A{i}'] = line
         
    # <<< تغییر کلیدی: افزودن پاورقی به فایل اکسل >>>
    # دو ردیف خالی فاصله می‌اندازیم
    footer_row = sheet.max_row + 3
    # سلول‌ها را برای زیبایی بیشتر ادغام می‌کنیم
    sheet.merge_cells(f'A{footer_row}:E{footer_row}')
    
    footer_cell = sheet[f'A{footer_row}']
    footer_cell.value = FOOTER_TEXT
    # متن را در سلول ادغام شده وسط‌چین می‌کنیم
    footer_cell.alignment = Alignment(horizontal='center')

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

# --- منطق اصلی و روت‌ها (بدون تغییر) ---
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
