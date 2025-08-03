# app.py (نسخه نهایی با ساختار تیتر/پاراگراف برای حل باگ رندرینگ)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

# --- کتابخانه برای ساخت PDF ---
from weasyprint import HTML, CSS

from docx import Document
from openpyxl import Workbook
from openpyxl.styles import Alignment

app = Flask(__name__)

# --- مسیر فونت و متن پاورقی (بدون تغییر) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE_NAME = "Vazirmatn-Regular.ttf"
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"


def create_pdf_with_weasyprint(text_content):
    """
    با استفاده از WeasyPrint یک PDF بی‌نقص با ساختار تیتر و پاراگراف می‌سازد.
    """
    print("--- Starting PDF creation with Heading/Paragraph structure ---")
    
    lines = text_content.strip().splitlines()
    
    # <<< تغییر کلیدی: جدا کردن خط اول به عنوان تیتر >>>
    heading_html = ""
    # اگر متنی وجود داشته باشد و خط اول خالی نباشد
    if lines and lines[0].strip():
        # خط اول را در یک تگ h2 (تیتر) قرار می‌دهیم
        heading_html = f'<h2 dir="auto">{lines[0].strip()}</h2>'

    # پردازش بقیه خطوط به عنوان پاراگراف
    paragraphs_html = ''.join([f'<p dir="auto">{line.strip()}</p>' for line in lines[1:] if line.strip()])
    
    # 1. ساخت قالب HTML کامل با استایل‌های جدید برای تیتر
    html_template = f"""
    <!DOCTYPE html>
    <html lang="fa">
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
                line-height: 1.8;
            }}
            
            /* استایل جدید برای تیتر */
            h2 {{
                font-size: 16pt;
                color: #333;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
                margin-bottom: 24px;
            }}
            
            p {{
                margin-top: 0;
                margin-bottom: 1em;
            }}

            /* استایل هوشمند برای چینش متن (برای تیتر و پاراگراف) */
            *[dir="rtl"] {{
                text-align: right;
            }}
            *[dir="ltr"] {{
                text-align: left;
            }}

            /* استایل پاورقی (بدون تغییر) */
            .footer {{
                position: fixed;
                bottom: 10px;
                left: 0;
                right: 0;
                text-align: center;
                color: #007bff; /* آبی */
                font-size: 10pt;
                direction: rtl;
            }}
        </style>
    </head>
    <body>
        {heading_html}
        {paragraphs_html}
        
        <div class="footer">
            {FOOTER_TEXT}
        </div>
    </body>
    </html>
    """
    
    try:
        html = HTML(string=html_template, base_url=BASE_DIR)
        pdf_bytes = html.write_pdf()
        print("--- PDF generated successfully with WeasyPrint ---")
        return io.BytesIO(pdf_bytes)

    except Exception:
        # ... بلوک خطا ...
        print("🔥🔥🔥 WEASYPRINT FAILED! See traceback below. 🔥🔥🔥")
        print(traceback.format_exc())
        error_html = f"<h1>Error</h1><p>Could not generate PDF. Please check server logs.</p>"
        return io.BytesIO(HTML(string=error_html).write_pdf())


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
