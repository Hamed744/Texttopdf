import os
import io
import traceback
from flask import Flask, request, send_file, render_template

# --- کتابخانه‌های استاندارد ساخت فایل ---
from weasyprint import HTML, CSS
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from openpyxl import Workbook
from openpyxl.styles import Alignment

# --- کتابخانه‌های کلیدی برای پردازش متن دو جهته (فارسی/انگلیسی) ---
import arabic_reshaper
from bidi.algorithm import get_display

app = Flask(__name__)

# --- مسیر فونت و متن پاورقی (بدون تغییر) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# مهم: برای پردازش صحیح، فونتی که از فارسی پشتیبانی می‌کند حیاتی است.
FONT_FILE_NAME = "Vazirmatn-Regular.ttf" 
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"


# --- تابع کمکی جدید برای پردازش و بازچینی متن ---
def process_bidi_text(text):
    """
    متن ورودی را با استفاده از کتابخانه‌های تخصصی برای نمایش صحیح bidi پردازش می‌کند.
    این تابع حروف فارسی را به هم متصل کرده و ترتیب کلمات را درست می‌کند.
    """
    # 1. شکل‌دهی به حروف عربی/فارسی (مثلاً 'س ل ا م' را به 'سلام' تبدیل می‌کند)
    reshaped_text = arabic_reshaper.reshape(text)
    # 2. بازچینی متن برای نمایش صحیح در محیط‌های چپ‌چین (LTR)
    bidi_text = get_display(reshaped_text)
    return bidi_text


# --- توابع ساخت فایل (اصلاح شده با منطق Bidi) ---

def create_pdf_with_weasyprint(text_content):
    """
    یک فایل PDF با پردازش دقیق Bidi برای هر خط ایجاد می‌کند.
    """
    print("--- Starting PDF creation with advanced Bidi processing ---")
    
    # پردازش هر خط به صورت جداگانه برای حفظ ساختار
    processed_lines = [process_bidi_text(line) for line in text_content.split('\n')]
    # تبدیل لیست خطوط به یک رشته HTML با تگ‌های <br>
    html_content = "<br>".join(processed_lines)

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
                text-align: right; /* چینش پیش‌فرض برای کل صفحه */
            }}
            /* استفاده از تگ div به جای pre برای کنترل بهتر */
            div.content {{
                white-space: pre-wrap; /* شکستن خطوط حفظ شود */
                direction: rtl;
            }}
            .footer {{
                position: fixed;
                bottom: 10px; left: 0; right: 0;
                text-align: center;
                color: #007bff;
                font-size: 10pt;
            }}
        </style>
    </head>
    <body>
        <div class="content">{html_content}</div>
        <div class="footer">{process_bidi_text(FOOTER_TEXT)}</div>
    </body>
    </html>
    """
    
    try:
        html = HTML(string=html_template, base_url=BASE_DIR)
        pdf_bytes = html.write_pdf()
        print("--- PDF generated successfully with Bidi processing ---")
        return io.BytesIO(pdf_bytes)
    except Exception:
        print("🔥🔥🔥 WEASYPRINT FAILED! See traceback below. 🔥🔥🔥")
        print(traceback.format_exc())
        error_html = "<h1>Error</h1><p>Could not generate PDF. Please check server logs.</p>"
        return io.BytesIO(HTML(string=error_html).write_pdf())


def create_docx(text_content):
    """
    یک فایل DOCX با پردازش Bidi برای هر پاراگراف ایجاد می‌کند.
    """
    document = Document()
    
    for line in text_content.split('\n'):
        # پردازش هر خط به صورت جداگانه
        processed_line = process_bidi_text(line)
        p = document.add_paragraph(processed_line)
        # همیشه پاراگراف را راست‌چین می‌کنیم، چون get_display ترتیب را درست کرده است
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    footer = document.sections[0].footer
    footer_p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_p.text = process_bidi_text(FOOTER_TEXT)
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer


def create_txt(text_content):
    """
    یک فایل TXT ساده ایجاد می‌کند. پردازش Bidi برای TXT معمولاً لازم نیست
    چون نمایش آن به ویرایشگر متن کاربر بستگی دارد.
    """
    full_content = f"{text_content}\n\n\n---\n{FOOTER_TEXT}"
    return io.BytesIO(full_content.encode('utf-8'))

    
def create_xlsx(text_content):
    """
    یک فایل XLSX با پردازش Bidi برای هر سلول ایجاد می‌کند.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.sheet_view.rightToLeft = True # شیت را راست‌به‌چپ می‌کنیم

    for i, line in enumerate(text_content.split('\n'), 1):
        cell = sheet[f'A{i}']
        cell.value = process_bidi_text(line) # متن پردازش شده را در سلول قرار می‌دهیم
        # چینش را راست می‌گذاریم
        cell.alignment = Alignment(horizontal='right', vertical='top', wrap_text=True)

    footer_row = sheet.max_row + 3
    sheet.merge_cells(f'A{footer_row}:E{footer_row}')
    footer_cell = sheet[f'A{footer_row}']
    footer_cell.value = process_bidi_text(FOOTER_TEXT)
    footer_cell.alignment = Alignment(horizontal='center')
    
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


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
