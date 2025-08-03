# app.py (نسخه نهایی در حالت تشخیصی برای حل قطعی مشکل)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

# --- کتابخانه‌ها (بدون تغییر) ---
import arabic_reshaper
from bidi.algorithm import get_display

from fpdf import FPDF
from docx import Document
from openpyxl import Workbook
from openpyxl.styles import Alignment

app = Flask(__name__)

# --- مسیر فونت و متن پاورقی (بدون تغییر) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "Vazirmatn-Regular.ttf")
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"

def prepare_persian_text(text):
    """تابع آماده‌سازی متن فارسی (بدون تغییر)"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def create_pdf(text_content):
    """
    تابع ساخت PDF با رویکرد تشخیصی و کادر قابل مشاهده
    """
    print("--- Starting PDF creation [DIAGNOSTIC MODE] ---")
    pdf = FPDF()
    pdf.add_page()
    
    try:
        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        pdf.set_font("Vazir", size=12)
        print("Font added and set successfully.")
        
        # 1. پردازش کل متن ورودی به صورت یکپارچه
        # استفاده از splitlines() برای سازگاری با انواع خطوط جدید
        cleaned_text = "\n".join(text_content.strip().splitlines())
        full_processed_text = prepare_persian_text(cleaned_text)
        
        # 2. نوشتن متن با یک کادر قابل مشاهده (border=1)
        print("Writing text to multi_cell with a visible border...")
        pdf.multi_cell(w=0, h=10, txt=full_processed_text, border=1, align='R')
        
        print("--- Text writing finished. ---")

        # 3. افزودن پاورقی
        pdf.set_y(-30)
        pdf.set_font("Vazir", size=10)
        pdf.set_text_color(0, 123, 255)
        processed_footer = prepare_persian_text(FOOTER_TEXT)
        pdf.cell(0, 10, txt=processed_footer, border=0, ln=1, align='C')
        
    except Exception:
        # ... بلوک خطا ...
        print("🔥🔥🔥 PDF CREATION FAILED! See traceback below. 🔥🔥🔥")
        print(traceback.format_exc())
        if not pdf.page_no(): pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'ERROR: Could not generate PDF. Please check server logs.', 0, 1, 'C')

    pdf_output = pdf.output()
    return io.BytesIO(pdf_output)

# --- بقیه فایل app.py (توابع دیگر و روت‌ها) بدون هیچ تغییری باقی می‌ماند ---

def create_docx(text_content):
    document = Document()
    p = document.add_paragraph(text_content)
    p.alignment = 3
    footer = document.sections[0].footer
    footer_p = footer.paragraphs[0]
    footer_p.text = FOOTER_TEXT
    footer_p.alignment = 1
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

def create_txt(text_content):
    full_content = f"{text_content}\n\n\n---\n{FOOTER_TEXT}"
    return io.BytesIO(full_content.encode('utf-8'))
    
def create_xlsx(text_content):
    workbook = Workbook()
    sheet = workbook.active
    sheet.sheet_view.rightToLeft = True
    for i, line in enumerate(text_content.split('\n'), 1):
         sheet[f'A{i}'] = line
    footer_row = sheet.max_row + 3
    sheet.merge_cells(f'A{footer_row}:E{footer_row}')
    footer_cell = sheet[f'A{footer_row}']
    footer_cell.value = FOOTER_TEXT
    footer_cell.alignment = Alignment(horizontal='center')
    buffer = io.BytesIO()
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
