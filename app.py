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

# --- کتابخانه لازم برای چسباندن حروف فارسی ---
import arabic_reshaper

app = Flask(__name__)

# --- ثابت‌ها ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE_NAME = "Vazirmatn-Regular.ttf"
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"


# --- توابع کمکی ---

def get_line_direction(line):
    """جهت یک خط را (rtl یا ltr) تشخیص می‌دهد."""
    if not line or line.isspace():
        return 'ltr'
    rtl_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F]')
    return 'rtl' if rtl_pattern.search(line) else 'ltr'

def reshape_rtl_text(line):
    """حروف فارسی را برای نمایش صحیح در رندرهای مختلف به هم می‌چسباند."""
    return arabic_reshaper.reshape(line)


# --- توابع اصلی ساخت فایل (منطق نهایی و اصلاح‌شده برای همه فرمت‌ها) ---

def create_pdf_with_weasyprint(text_content):
    """PDF را با چسباندن حروف فارسی ایجاد می‌کند."""
    content_html_parts = []
    for line in text_content.split('\n'):
        if not line.strip():
            content_html_parts.append('<div> </div>')
            continue
        direction = get_line_direction(line)
        if direction == 'rtl':
            reshaped_line = reshape_rtl_text(line)
            content_html_parts.append(f'<div class="rtl">{reshaped_line}</div>')
        else:
            content_html_parts.append(f'<div class="ltr">{line}</div>')
    final_html_content = "\n".join(content_html_parts)
    html_template = f"""
    <!DOCTYPE html><html lang="fa"><head><meta charset="UTF-8">
    <style>
        @font-face {{ font-family: 'Vazir'; src: url('{FONT_FILE_NAME}'); }}
        body {{ font-family: 'Vazir', sans-serif; font-size: 12pt; line-height: 1.8; }}
        .rtl {{ text-align: right; direction: rtl; }}
        .ltr {{ text-align: left; direction: ltr; }}
        .footer {{ position: fixed; bottom: 10px; left: 0; right: 0; text-align: center; color: #007bff; font-size: 10pt; }}
    </style></head><body>{final_html_content}
    <div class="footer rtl">{reshape_rtl_text(FOOTER_TEXT)}</div></body></html>
    """
    try:
        html = HTML(string=html_template, base_url=BASE_DIR)
        return io.BytesIO(html.write_pdf())
    except Exception:
        print(f"🔥🔥🔥 WEASYPRINT FAILED! 🔥🔥🔥\n{traceback.format_exc()}")
        return io.BytesIO(b"Error generating PDF.")


def create_docx(text_content):
    """
    DOCX را با چسباندن حروف فارسی ایجاد می‌کند تا در همه نمایشگرها صحیح دیده شود.
    """
    document = Document()
    for line in text_content.split('\n'):
        direction = get_line_direction(line)
        if not line.strip():
            document.add_paragraph()
            continue

        if direction == 'rtl':
            # <<< این خط، مشکل DOCX را حل می‌کند >>>
            processed_line = reshape_rtl_text(line)
            p = document.add_paragraph(processed_line)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p.paragraph_format.right_to_left = True
        else:
            p = document.add_paragraph(line)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.right_to_left = False

    footer = document.sections[0].footer
    footer_p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    # پاورقی هم نیاز به پردازش دارد
    footer_p.text = reshape_rtl_text(FOOTER_TEXT)
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_p.paragraph_format.right_to_left = True
    
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer


def create_xlsx(text_content):
    """
    XLSX را برای سازگاری بیشتر، با حروف فارسی چسبیده ایجاد می‌کند.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.sheet_view.rightToLeft = True

    for i, line in enumerate(text_content.split('\n'), 1):
        cell = sheet[f'A{i}']
        direction = get_line_direction(line)
        
        if direction == 'rtl':
            # پردازش برای اکسل هم جهت اطمینان انجام می‌شود
            cell.value = reshape_rtl_text(line)
            cell.alignment = Alignment(horizontal='right', vertical='top', wrap_text=True)
        else:
            cell.value = line
            cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

    footer_row = sheet.max_row + 3
    sheet.merge_cells(f'A{footer_row}:E{footer_row}')
    footer_cell = sheet[f'A{footer_row}']
    footer_cell.value = reshape_rtl_text(FOOTER_TEXT)
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
