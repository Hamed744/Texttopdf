import os
import io
import traceback
import re
from flask import Flask, request, send_file, render_template

# --- کتابخانه‌ها ---
from weasyprint import HTML, CSS
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
# openpyxl دیگر لازم نیست، می‌توانید آن را از requirements.txt هم حذف کنید
import arabic_reshaper

app = Flask(__name__)

# --- ثابت‌ها ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE_NAME = "Vazirmatn-Regular.ttf"
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"

# --- توابع کمکی (بدون تغییر) ---
def get_line_direction(line):
    if not line or line.isspace(): return 'ltr'
    rtl_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F]')
    return 'rtl' if rtl_pattern.search(line) else 'ltr'

def reshape_rtl_text(line):
    return arabic_reshaper.reshape(line)

# --- توابع ساخت فایل (اصلاح شده) ---

def get_html_template(text_content):
    """یک تابع مشترک که بدنه HTML را برای PDF و HTML می‌سازد."""
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
    
    return f"""
    <!DOCTYPE html><html lang="fa"><head><meta charset="UTF-8">
    <title>Exported File</title>
    <style>
        @font-face {{ font-family: 'Vazir'; src: url('{FONT_FILE_NAME}'); }}
        body {{ font-family: 'Vazir', sans-serif; font-size: 12pt; line-height: 1.8; max-width: 800px; margin: 2rem auto; padding: 1rem; border: 1px solid #ddd; }}
        .rtl {{ text-align: right; direction: rtl; }}
        .ltr {{ text-align: left; direction: ltr; }}
        .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; text-align: center; color: #007bff; font-size: 10pt; }}
    </style></head><body>{final_html_content}
    <div class="footer rtl">{reshape_rtl_text(FOOTER_TEXT)}</div></body></html>
    """

def create_pdf_with_weasyprint(text_content):
    html_string = get_html_template(text_content)
    try:
        # در PDF، پاورقی را با position:fixed استایل می‌دهیم
        html_string = html_string.replace(
            '.footer {', 
            '.footer { position: fixed; bottom: 10px; left: 0; right: 0; border: none;'
        )
        html = HTML(string=html_string, base_url=BASE_DIR)
        return io.BytesIO(html.write_pdf())
    except Exception:
        print(f"🔥🔥🔥 WEASYPRINT FAILED! 🔥🔥🔥\n{traceback.format_exc()}")
        return io.BytesIO(b"Error generating PDF.")

def create_docx(text_content):
    document = Document()
    for line in text_content.split('\n'):
        direction = get_line_direction(line)
        if not line.strip():
            document.add_paragraph()
            continue
        if direction == 'rtl':
            p = document.add_paragraph(reshape_rtl_text(line))
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p.paragraph_format.right_to_left = True
        else:
            p = document.add_paragraph(line)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.right_to_left = False
    footer = document.sections[0].footer
    footer_p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_p.text = reshape_rtl_text(FOOTER_TEXT)
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_p.paragraph_format.right_to_left = True
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

def create_txt(text_content):
    full_content = f"{text_content}\n\n\n---\n{FOOTER_TEXT}"
    return io.BytesIO(full_content.encode('utf-8'))

# ***** تابع جدید برای ساخت HTML *****
def create_html(text_content):
    """یک فایل HTML قابل نمایش در مرورگر ایجاد می‌کند."""
    html_string = get_html_template(text_content)
    return io.BytesIO(html_string.encode('utf-8'))


# --- تابع پردازشگر اصلی درخواست (اصلاح شده) ---
def process_request(content, file_format):
    if file_format == 'pdf':
        buffer = create_pdf_with_weasyprint(content)
        filename = 'export.pdf'
        mimetype = 'application/pdf'
    elif file_format == 'docx':
        buffer = create_docx(content)
        filename = 'export.docx'
        mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    # ***** اینجا XLSX با HTML جایگزین شده است *****
    elif file_format == 'html':
        buffer = create_html(content)
        filename = 'export.html'
        mimetype = 'text/html'
    else: # پیش‌فرض txt
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
