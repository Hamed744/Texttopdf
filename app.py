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
    ساخت PDF با تشخیص خودکار جهت متن برای هر پاراگراف
    """
    print("--- Starting PDF creation with auto LTR/RTL detection ---")
    
    # <<< تغییر کلیدی: افزودن dir="auto" به پاراگراف‌ها و اصلاح CSS >>>
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
                line-height: 1.8;
            }}
            
            p {{
                /* باعث می‌شود پاراگراف‌ها در هر دو حالت زیبا به نظر برسند */
                text-align: justify;
                margin-top: 0;
                margin-bottom: 1em;
            }}
            
            /* این دو خط مهم‌ترین بخش استایل جدید هستند */
            p[dir="rtl"] {{ text-align: right; }}
            p[dir="ltr"] {{ text-align: left; }}

            .footer {{
                position: fixed;
                bottom: 10px;
                left: 0;
                right: 0;
                text-align: center;
                color: #007bff;
                font-size: 10pt;
            }}
        </style>
    </head>
    <body>
        <!-- برای هر پاراگراف از dir="auto" استفاده می‌کنیم تا جهت آن هوشمندانه تعیین شود -->
        {''.join([f'<p dir="auto">{line}</p>' for line in text_content.strip().splitlines() if line.strip()])}
        
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
        print("🔥🔥🔥 WEASYPRINT FAILED! See traceback below. 🔥🔥🔥")
        print(traceback.format_exc())
        error_html = f"<h1>Error</h1><p>Could not generate PDF. Please check server logs.</p>"
        return io.BytesIO(HTML(string=error_html).write_pdf())


# --- بقیه فایل app.py (توابع دیگر و روت‌ها) بدون هیچ تغییری باقی می‌ماند ---

def create_docx(text_content):
    document = Document()
    p = document.add_paragraph(text_content)
    # در ورد، تشخیص خودکار جهت متن پیچیده‌تر است و فعلا به صورت پیش‌فرض راست‌چین باقی می‌ماند
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
