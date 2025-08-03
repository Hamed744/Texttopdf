# app.py (نسخه نهایی با افزودن پاورقی به تمام فایل‌ها)

import os
import io
import traceback
from flask import Flask, request, send_file, render_template

# --- کتابخانه‌های ضروری برای فارسی (بدون تغییر) ---
import arabic_reshaper
from bidi.algorithm import get_display

# --- کتابخانه‌های اصلی فایل‌ها ---
from fpdf import FPDF
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

app = Flask(__name__)

# --- مسیر فونت و متن پاورقی ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "Vazirmatn-Regular.ttf")
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"

def prepare_persian_text(text):
    """تابع آماده‌سازی متن فارسی"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def create_pdf(text_content):
    """ساخت PDF با افزودن پاورقی در انتهای آخرین صفحه"""
    pdf = FPDF()
    pdf.add_page()
    
    try:
        # --- بخش تنظیم فونت ---
        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        
        # --- نوشتن محتوای اصلی ---
        lines = text_content.strip().split('\n')
        title = lines[0].strip() if lines else ""
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        if title:
            pdf.set_font("Vazir", size=18)
            pdf.cell(0, 15, txt=prepare_persian_text(title), border=0, ln=1, align='C')
            pdf.ln(5)

        if body:
            pdf.set_font("Vazir", size=12)
            pdf.multi_cell(0, 10, txt=prepare_persian_text(body), border=0, align='R')

        # --- <<< تغییر کلیدی: افزودن پاورقی >>> ---
        # به پایین صفحه می‌رویم (20 میلی‌متر از لبه پایین)
        pdf.set_y(-20)
        pdf.set_font("Vazir", size=10)
        # رنگ متن را آبی می‌کنیم
        pdf.set_text_color(0, 102, 204)
        # متن پاورقی را پردازش و به صورت وسط‌چین اضافه می‌کنیم
        processed_footer = prepare_persian_text(FOOTER_TEXT)
        pdf.cell(0, 10, txt=processed_footer, border=0, ln=1, align='C')
        # رنگ متن را به حالت پیش‌فرض (سیاه) برمی‌گردانیم
        pdf.set_text_color(0, 0, 0)

    except Exception:
        # بلوک مدیریت خطا
        print(f"🔥🔥🔥 PDF CREATION FAILED! See traceback below. 🔥🔥🔥\n{traceback.format_exc()}")
        if not pdf.page_no(): pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ERROR: Could not generate PDF.', 0, 1, 'C')

    return pdf.output()

def create_docx(text_content):
    """ساخت DOCX با افزودن پاورقی"""
    document = Document()
    document.add_paragraph(text_content)
    
    # --- افزودن پاورقی ---
    document.add_paragraph('') # یک خط خالی برای فاصله
    footer_p = document.add_paragraph()
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer_p.add_run(FOOTER_TEXT)
    font = run.font
    font.color.rgb = RGBColor(0, 102, 204)
    
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

def create_txt(text_content):
    """ساخت TXT با افزودن پاورقی"""
    full_content = f"{text_content}\n\n--------------------\n{FOOTER_TEXT}"
    return io.BytesIO(full_content.encode('utf-8'))

def create_xlsx(text_content):
    """ساخت XLSX با افزودن پاورقی"""
    workbook = Workbook()
    sheet = workbook.active
    sheet.sheet_view.rightToLeft = True
    
    lines = text_content.split('\n')
    for i, line in enumerate(lines, 1):
         sheet[f'A{i}'] = line
    
    # --- افزودن پاورقی ---
    footer_row = len(lines) + 3 # با دو خط فاصله
    footer_cell = sheet[f'A{footer_row}']
    footer_cell.value = FOOTER_TEXT
    footer_cell.font = Font(color="0066CC", bold=True)
    footer_cell.alignment = Alignment(horizontal='center')
    # ادغام چند سلول برای نمایش بهتر پاورقی
    sheet.merge_cells(start_row=footer_row, start_column=1, end_row=footer_row, end_column=5)

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

# --- منطق اصلی پردازش درخواست (با تغییر کوچک در خروجی PDF) ---
def process_request(content, file_format):
    try:
        if file_format == 'pdf':
            pdf_output_bytes = create_pdf(content)
            buffer = io.BytesIO(pdf_output_bytes)
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
    except Exception:
        print(f"🔥🔥🔥 An uncaught error occurred in process_request for format '{file_format}' 🔥🔥🔥\n{traceback.format_exc()}")
        return "An internal server error occurred while generating the file.", 500

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
