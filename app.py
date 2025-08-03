# app.py (نسخه نهایی با تشخیص خودکار جهت متن LTR/RTL)

import os
import io
import traceback
from flask import Flask, request, jsonify, send_file, render_template

# --- کتابخانه جدید برای ساخت PDF ---
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
    با استفاده از WeasyPrint از متن یک PDF زیبا و بی‌نقص می‌سازد.
    این نسخه جهت متن را به صورت خودکار تشخیص می‌دهد.
    """
    print("--- Starting PDF creation with WeasyPrint (Auto-direction) ---")
    
    # <<< تغییر کلیدی: افزودن dir="auto" به هر پاراگراف >>>
    # ما دیگر جهت کلی سند را rtl نمی‌کنیم، بلکه به هر پاراگراف اجازه می‌دهیم جهت خود را پیدا کند.
    paragraphs_html = ''.join([f'<p dir="auto">{line}</p>' for line in text_content.strip().splitlines() if line.strip()])
    
    # 1. ساخت یک قالب HTML کامل و زیبا با استفاده از CSS
    html_template = f"""
    <!DOCTYPE html>
    <html lang="fa">
    <head>
        <meta charset="UTF-8">
        <style>
            /* تعریف فونت وزیر برای استفاده در کل سند */
            @font-face {{
                font-family: 'Vazir';
                src: url('{FONT_FILE_NAME}');
            }}

            body {{
                font-family: 'Vazir', sans-serif;
                font-size: 12pt;
                line-height: 1.8;
            }}
            
            /* <<< تغییر کلیدی: استایل‌دهی هوشمند بر اساس جهت متن >>> */
            /* پاراگراف‌های راست‌چین (فارسی) */
            p[dir="rtl"] {{
                text-align: right;
            }}
            /* پاراگراف‌های چپ‌چین (انگلیسی) */
            p[dir="ltr"] {{
                text-align: left;
            }}
            
            p {{
                margin-top: 0;
                margin-bottom: 1em;
            }}

            /* استایل پاورقی (پاورقی همیشه راست‌چین است) */
            .footer {{
                position: fixed;
                bottom: 10px;
                left: 0;
                right: 0;
                text-align: center;
                color: #007bff; /* آبی */
                font-size: 10pt;
                direction: rtl; /* جهت پاورقی ثابت است */
            }}
        </style>
    </head>
    <body>
        {paragraphs_html}
        
        <!-- افزودن پاورقی -->
        <div class="footer">
            {FOOTER_TEXT}
        </div>
    </body>
    </html>
    """
    
    try:
        # 2. رندر کردن HTML به PDF
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
    # در ورد، تشخیص خودکار سخت‌تر است و معمولاً کل سند یک جهت دارد
    p.alignment = 3 # WD_ALIGN_PARAGRAPH.RIGHT
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
