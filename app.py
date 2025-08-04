import os
import io
import traceback
import re
from flask import Flask, request, send_file, render_template
from flask_cors import CORS  # --- این خط اضافه شده است ---

# --- کتابخانه‌های اصلی ---
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from weasyprint import HTML, CSS
import arabic_reshaper

# --- کتابخانه جدید و کلیدی برای تبدیل HTML به DOCX ---
from htmldocx import HtmlToDocx

app = Flask(__name__)
CORS(app)  # --- این خط اضافه شده است تا به همه دامنه‌ها اجازه دسترسی بدهد ---

# --- ثابت‌ها ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE_NAME = "Vazirmatn-Regular.ttf"
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"


# --- توابع کمکی ---
def get_line_direction(line):
    if not line or line.isspace(): return 'ltr'
    rtl_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F]')
    return 'rtl' if rtl_pattern.search(line) else 'ltr'

def reshape_rtl_text(line):
    return arabic_reshaper.reshape(line)

# --- توابع ساخت فایل ---

def get_base_html_for_conversion(text_content):
    """
    یک رشته HTML پایه تولید می‌کند که هم برای PDF و هم برای DOCX قابل استفاده است.
    """
    content_html_parts = []
    for line in text_content.split('\n'):
        if not line.strip():
            content_html_parts.append('<p> </p>')
            continue
        direction = get_line_direction(line)
        if direction == 'rtl':
            reshaped_line = reshape_rtl_text(line)
            content_html_parts.append(f'<p style="text-align: right; direction: rtl;">{reshaped_line}</p>')
        else:
            content_html_parts.append(f'<p style="text-align: left; direction: ltr;">{line}</p>')
    return "\n".join(content_html_parts)


def create_docx(text_content):
    """
    DOCX را با تبدیل مستقیم از HTML ایجاد می‌کند.
    """
    print("--- DOCX Creation: Using HTML to DOCX conversion method ---")
    document = Document()
    parser = HtmlToDocx()
    html_content = get_base_html_for_conversion(text_content)
    parser.add_html_to_document(html_content, document)
    footer = document.sections[0].footer
    footer_p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_p.text = reshape_rtl_text(FOOTER_TEXT)
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

def create_pdf_with_weasyprint(text_content):
    """
    PDF را از روی یک قالب کامل HTML با فونت سفارشی ایجاد می‌کند.
    """
    html_body = get_base_html_for_conversion(text_content)
    reshaped_footer = reshape_rtl_text(FOOTER_TEXT)
    full_html = f"""
    <!DOCTYPE html><html lang="fa"><head><meta charset="UTF-8"><title>Exported PDF</title>
    <style>
        @font-face {{ font-family: 'Vazir'; src: url('{FONT_FILE_NAME}'); }}
        body {{ font-family: 'Vazir', sans-serif; font-size: 12pt; line-height: 1.8; }}
        p {{ margin: 0; padding: 0; }}
        .footer {{ position: fixed; bottom: 10px; left: 0; right: 0; text-align: center; color: #007bff; font-size: 10pt; font-family: 'Vazir', sans-serif; }}
    </style></head><body>{html_body}
    <div class="footer">{reshaped_footer}</div></body></html>
    """
    try:
        html = HTML(string=full_html, base_url=BASE_DIR)
        return io.BytesIO(html.write_pdf())
    except Exception:
        print(f"🔥🔥🔥 WEASYPRINT FAILED! 🔥🔥🔥\n{traceback.format_exc()}")
        return io.BytesIO(b"Error generating PDF.")

def create_txt(text_content):
    full_content = f"{text_content}\n\n\n---\n{FOOTER_TEXT}"
    return io.BytesIO(full_content.encode('utf-8'))

def create_html(text_content):
    """یک فایل HTML قابل نمایش در مرورگر با استایل‌های کامل ایجاد می‌کند."""
    html_body = get_base_html_for_conversion(text_content)
    reshaped_footer = reshape_rtl_text(FOOTER_TEXT)
    full_html = f"""
    <!DOCTYPE html><html lang="fa"><head><meta charset="UTF-8"><title>Exported File</title>
    <style>
        body {{ font-size: 12pt; line-height: 1.8; max-width: 800px; margin: 2rem auto; padding: 2rem; border: 1px solid #ddd; font-family: sans-serif; }}
        p {{ margin: 0; padding: 0 0 0.5em 0; }}
        .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; text-align: center; color: #007bff; font-size: 10pt; }}
    </style></head><body>{html_body}
    <div class="footer">{reshaped_footer}</div></body></html>
    """
    return io.BytesIO(full_html.encode('utf-8'))

# --- تابع پردازشگر اصلی درخواست ---
def process_request(content, file_format):
    actions = {'pdf': create_pdf_with_weasyprint, 'docx': create_docx, 'html': create_html, 'txt': create_txt}
    buffer_func = actions.get(file_format, create_txt)
    buffer = buffer_func(content)
    mimetypes = {'pdf': 'application/pdf', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'html': 'text/html', 'txt': 'text/plain'}
    mimetype = mimetypes.get(file_format, 'text/plain')
    filename = f'export.{file_format}'
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)


# --- ***** تغییر اصلی برای پشتیبانی از Render در اینجا اعمال شده است ***** ---
@app.route('/', methods=['GET', 'POST', 'HEAD'])
def index():
    # اگر درخواست از نوع HEAD بود (برای Health Check سرویس Render)
    # یک پاسخ موفقیت‌آمیز و خالی برگردان
    if request.method == 'HEAD':
        return '', 200

    # اگر درخواست از نوع POST بود (کاربر دکمه ساخت فایل را زده)
    if request.method == 'POST':
        content = request.form.get('content')
        file_format = request.form.get('format', 'txt').lower()
        if not content:
            return "لطفا متنی برای تبدیل وارد کنید.", 400
        return process_request(content, file_format)
    
    # در غیر این صورت، درخواست GET است و باید صفحه اصلی نمایش داده شود
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
