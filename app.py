# app.py (نسخه جدید با لاگ‌گیری پیشرفته)

import io
import base64
import traceback # کتابخانه جدید برای چاپ کامل خطا
from flask import Flask, request, jsonify, send_file, render_template
from fpdf import FPDF
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- PASTE YOUR BASE64 FONT STRING HERE ---
# مطمئن شوید که رشته کامل و بدون هیچ تغییری اینجا کپی شده است
VAZIR_FONT_BASE64 = """
اینجا رشته طولانی که از فایل font_base64.txt کپی کرده‌اید را جای‌گذاری کنید
"""
# ---

def create_pdf(text_content):
    print("--- Starting PDF creation ---")
    pdf = FPDF()
    pdf.add_page()
    
    try:
        print("Step 1: Decoding Base64 font string...")
        # مطمئن می‌شویم که فضای خالی اضافی در ابتدا و انتهای رشته حذف شود
        font_string_stripped = VAZIR_FONT_BASE64.strip()
        if not font_string_stripped:
            raise ValueError("VAZIR_FONT_BASE64 variable is empty!")
            
        font_data = base64.b64decode(font_string_stripped)
        print(f"Step 2: Successfully decoded {len(font_data)} bytes of font data.")
        
        # استفاده از io.BytesIO برای خواندن داده‌های بایت فونت
        font_stream = io.BytesIO(font_data)
        
        print("Step 3: Adding font to FPDF object...")
        pdf.add_font('Vazir', '', font_stream, uni=True)
        print("Step 4: Setting PDF font to Vazir...")
        pdf.set_font('Vazir', '', 12)
        pdf.set_right_to_left(True)
        print("--- Font embedding successful ---")

    except Exception as e:
        print("🔥🔥🔥 FONT EMBEDDING FAILED! 🔥🔥🔥")
        # چاپ کامل خطا در لاگ برای دیباگ
        print(traceback.format_exc())
        
        print("Falling back to default Arial font.")
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'WARNING: Persian font could not be loaded. Please check server logs.', 0, 1, 'C')
        pdf.set_font('Arial', '', 12)

    print("Step 5: Writing text content to PDF...")
    pdf.multi_cell(0, 10, text_content)
    
    print("Step 6: Generating PDF output bytes...")
    pdf_output = pdf.output()
    buffer = io.BytesIO(pdf_output)
    buffer.seek(0)
    print("--- PDF creation finished ---")
    return buffer

# --- سایر توابع بدون تغییر باقی می‌مانند ---
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
        else: # txt
            buffer = create_txt(content)
            filename = 'export.txt'
            mimetype = 'text/plain'

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
    except Exception as e:
        print(f"🔥🔥🔥 Error in process_request for format '{file_format}' 🔥🔥🔥")
        print(traceback.format_exc())
        # این پیام خطا در مرورگر کاربر نمایش داده می‌شود
        return "An internal server error occurred while generating the file.", 500

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        file_format = request.form.get('format', 'txt').lower()
        if not content:
            return "لطفا متنی برای تبدیل وارد کنید.", 400
        # تمام منطق پردازش به process_request منتقل شد تا خطاها در آنجا مدیریت شوند
        return process_request(content, file_format)
    return render_template('index.html')

# API route remains the same for now
@app.route('/convert', methods=['POST'])
def convert_text_api():
    data = request.json
    content = data.get('content')
    file_format = data.get('format', 'txt').lower()
    if not content:
        return jsonify({"error": "No content provided"}), 400
    return process_request(content, file_format)


if __name__ == '__main__':
    app.run(debug=True)
