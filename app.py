import os
import io
import traceback
import re
from flask import Flask, request, send_file, render_template

# --- کتابخانه‌های ساخت فایل ---
from weasyprint import HTML, CSS
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from openpyxl import Workbook
from openpyxl.styles import Alignment

# --- کتابخانه‌های پردازش متن دو جهته ---
import arabic_reshaper
from bidi.algorithm import get_display

app = Flask(__name__)

# --- ثابت‌ها ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE_NAME = "Vazirmatn-Regular.ttf"
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"

# --- توابع کمکی ---

def get_line_direction(line):
    """
    جهت اصلی یک خط را بر اساس وجود کاراکترهای فارسی/عربی تشخیص می‌دهد.
    """
    rtl_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F]')
    return 'rtl' if rtl_pattern.search(line) else 'ltr'

def process_rtl_line(line):
    """
    یک خط راست‌به‌چپ را برای نمایش صحیح، شکل‌دهی و بازچینی می‌کند.
    """
    reshaped_text = arabic_reshaper.reshape(line)
    return get_display(reshaped_text)

# --- توابع اصلی ساخت فایل (منطق جدید و اصلاح‌شده) ---

def create_pdf_with_weasyprint(text_content):
    """
    PDF را با تعیین جهت و چینش برای هر خط به صورت مجزا ایجاد می‌کند.
    """
    print("--- PDF Creation: Processing each line individually ---")
    
    content_html_parts = []
    for line in text_content.split('\n'):
        direction = get_line_direction(line)
        if direction == 'rtl':
            # خطوط فارسی/ترکیبی را پردازش و در یک div راست‌چین قرار بده
            processed_line = process_rtl_line(line)
            content_html_parts.append(f'<div class="rtl">{processed_line}</div>')
        else:
            # خطوط انگلیسی را دست‌نخورده در یک div چپ‌چین قرار بده
            content_html_parts.append(f'<div class="ltr">{line}</div>')
    
    final_html_content = "\n".join(content_html_parts)
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            @font-face {{
                font-family: 'Vazir';
                src: url('{FONT_FILE_NAME}');
            }}
            body {{
                font-family: 'Vazir', sans-serif;
                font-size: 12pt;
                line-height: 1.6;
            }}
            /* کلید حل مشکل: استایل‌دهی مجزا برای هر جهت */
            .rtl {{
                text-align: right;
                direction: rtl;
            }}
            .ltr {{
                text-align: left;
                direction: ltr;
            }}
            .footer {{
                position: fixed; bottom: 10px; left: 0; right: 0;
                text-align: center; color: #007bff; font-size: 10pt;
            }}
        </style>
    </head>
    <body>
        {final_html_content}
        <div class="footer rtl">{process_rtl_line(FOOTER_TEXT)}</div>
    </body>
    </html>
    """
    try:
        html = HTML(string=html_template, base_url=BASE_DIR)
        return io.BytesIO(html.write_pdf())
    except Exception:
        print(f"🔥🔥🔥 WEASYPRINT FAILED! 🔥🔥🔥\n{traceback.format_exc()}")
        return io.BytesIO(b"Error generating PDF.")

def create_docx(text_content):
    """
    DOCX را با تعیین جهت و چینش برای هر پاراگراف به صورت مجزا ایجاد می‌کند.
    """
    document = Document()
    for line in text_content.split('\n'):
        direction = get_line_direction(line)
        
        # اگر خط خالی است، فقط یک پاراگراف خالی اضافه کن
        if not line.strip():
            document.add_paragraph()
            continue

        if direction == 'rtl':
            processed_line = process_rtl_line(line)
            p = document.add_paragraph(processed_line)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p.paragraph_format.right_to_left = True
        else:
            p = document.add_paragraph(line)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.right_to_left = False

    footer = document.sections[0].footer
    footer_p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_p.text = process_rtl_line(FOOTER_TEXT)
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

def create_xlsx(text_content):
    """
    XLSX را با تعیین جهت و چینش برای هر سلول به صورت مجزا ایجاد می‌کند.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.sheet_view.rightToLeft = True # نمای کلی شیت راست‌به‌چپ باشد

    for i, line in enumerate(text_content.split('\n'), 1):
        cell = sheet[f'A{i}']
        direction = get_line_direction(line)
        
        if direction == 'rtl':
            cell.value = process_rtl_line(line)
            cell.alignment = Alignment(horizontal='right', vertical='top', wrap_text=True)
        else:
            cell.value = line
            cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

    footer_row = sheet.max_row + 3
    sheet.merge_cells(f'A{footer_row}:E{footer_row}')
    footer_cell = sheet[f'A{footer_row}']
    footer_cell.value = process_rtl_line(FOOTER_TEXT)
    footer_cell.alignment = Alignment(horizontal='center')
    
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

def create_txt(text_content):
    full_content = f"{text_content}\n\n\n---\n{FOOTER_TEXT}"
    return io.BytesIO(full_content.encode('utf-8'))

# --- توابع مربوط به Flask (بدون تغییر) ---
def process_request(content, file_format):
    if file_format == 'pdf':
        buffer = create_pdf_with_weasyprint(content)
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
