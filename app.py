# app.py (نسخه نهایی با اصلاح مشکل فونت در HTML)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- محاسبه مسیر مطلق فایل فونت (صحیح و بدون تغییر) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "Vazirmatn-Regular.ttf")

def beautify_text_to_html(plain_text):
    """
    این تابع متن ساده را به یک قطعه HTML استایل‌بندی شده تبدیل می‌کند.
    """
    lines = plain_text.strip().split('\n')
    
    # ساخت بدنه HTML
    html_body = ""
    if lines:
        # خط اول به عنوان تیتر H1
        html_body += f"<h1>{lines[0]}</h1>"
        # بقیه خطوط به عنوان پاراگراف
        for line in lines[1:]:
            if line.strip():
                html_body += f"<p>{line.strip()}</p>"

    # <<< تغییر: ساختار HTML ساده‌تر شد >>>
    # فقط یک div اصلی با استایل و محتوا برمی‌گردانیم
    # این برای پارسر fpdf2 بهتر است
    full_html = f'''
    <div dir="rtl" style="font-family: Vazir; font-size: 12pt; line-height: 1.8; color: #333; text-align: justify;">
        <h1 style="color: #1095c1; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; margin-bottom: 20px; text-align: right;">{lines[0] if lines else ''}</h1>
        {''.join([f"<p>{line.strip()}</p>" for line in lines[1:] if line.strip()])}
    </div>
    '''
    return full_html


def create_pdf(html_content):
    print("--- Starting PDF creation ---")
    pdf = FPDF()
    pdf.add_page()
    
    try:
        print(f"Loading font from: {FONT_PATH}")
        if not os.path.exists(FONT_PATH):
            raise FileNotFoundError(f"Font file not found at path: {FONT_PATH}")

        pdf.add_font('Vazir', '', FONT_PATH, uni=True)
        print("Font added successfully.")
        
        # <<< تغییر کلیدی و راه‌حل نهایی >>>
        # قبل از رندر HTML، فونت فعال را به صورت اجباری روی "وزیر" تنظیم می‌کنیم
        pdf.set_font("Vazir", size=12)
        
        print("Rendering HTML content with Vazir font forced...")
        pdf.write_html(html_content)
        
        print("--- HTML rendering successful ---")

    except Exception:
        print("🔥🔥🔥 PDF CREATION FAILED! See traceback below. 🔥🔥🔥")
        print(traceback.format_exc())
        
        # <<< تغییر: بلوک خطا امن‌تر شد >>>
        # برای جلوگیری از خطای ثانویه، یک صفحه جدید باز می‌کنیم
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

# --- بقیه توابع و روت‌ها بدون هیچ تغییری باقی می‌مانند ---

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
    try:
        if file_format == 'pdf':
            html_output = beautify_text_to_html(content)
            buffer = create_pdf(html_output)
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

if __name__ == '__main__':
    app.run(debug=True)
