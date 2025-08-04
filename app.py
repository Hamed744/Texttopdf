import os
import io
import traceback
import re
import json
import requests
from flask import Flask, request, send_file, render_template
from flask_cors import CORS

from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from weasyprint import HTML, CSS
import arabic_reshaper
from bidi.algorithm import get_display

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE_NAME = "Vazirmatn-Regular.ttf"
FOOTER_TEXT = "هوش مصنوعی آلفا دانلود از گوگل پلی"

# --- توابع کمکی ---
def reshape_text(text):
    if not text:
        return ""
    return get_display(arabic_reshaper.reshape(text))

# --- توابع جدید برای ساخت فایل از داده‌های ساختاریافته (JSON) ---

def create_html_from_data(data, is_for_pdf=False):
    title = data.get('title', 'گفتگو')
    messages = data.get('messages', [])
    
    html_parts = []
    for msg in messages:
        role = "کاربر" if msg.get('role') == 'user' else "مدل"
        text = msg.get('text', '')
        images = msg.get('images', [])
        
        style = "background-color: #eef; border-right: 3px solid #6c757d;" if role == "کاربر" else "background-color: #f8f9fa; border-right: 3px solid #dee2e6;"
        
        html_parts.append(f'<div class="message" style="{style}">')
        html_parts.append(f'<strong>{reshape_text(role)}:</strong>')
        
        if text:
            reshaped_text_content = reshape_text(text).replace('\n', '<br>')
            html_parts.append(f'<p>{reshaped_text_content}</p>')
            
        if images and is_for_pdf:
            html_parts.append('<div class="image-container">')
            for img_url in images:
                html_parts.append(f'<img src="{img_url}" alt="Image from chat">')
            html_parts.append('</div>')
            
        html_parts.append('</div>')
        
    chat_html = "\n".join(html_parts)
    reshaped_footer = reshape_text(FOOTER_TEXT)
    
    font_url = f"file://{os.path.join(BASE_DIR, FONT_FILE_NAME)}" if is_for_pdf else FONT_FILE_NAME

    full_html = f"""
    <!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="UTF-8"><title>{reshape_text(title)}</title>
    <style>
        @font-face {{ font-family: 'Vazir'; src: url('{font_url}'); }}
        body {{ font-family: 'Vazir', sans-serif; font-size: 11pt; line-height: 1.8; max-width: 800px; margin: 1rem auto; padding: 1rem; border: 1px solid #ddd; }}
        h1 {{ text-align: center; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .message {{ padding: 10px; margin-bottom: 10px; border-radius: 8px; }}
        .message p {{ margin-top: 5px; white-space: pre-wrap; word-wrap: break-word; }}
        .image-container {{ margin-top: 10px; }}
        .image-container img {{ max-width: 100%; height: auto; border-radius: 5px; margin-bottom: 10px; border: 1px solid #ccc; }}
        .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; text-align: center; color: #007bff; font-size: 9pt; }}
    </style></head>
    <body><h1>{reshape_text(title)}</h1>{chat_html}<div class="footer">{reshaped_footer}</div></body></html>
    """
    return full_html

def create_pdf_from_data(data):
    full_html = create_html_from_data(data, is_for_pdf=True)
    return io.BytesIO(HTML(string=full_html, base_url=BASE_DIR).write_pdf())

def create_docx_from_data(data):
    document = Document()
    document.add_heading(reshape_text(data.get('title', 'گفتگو')), level=1)
    for msg in data.get('messages', []):
        role = "کاربر" if msg.get('role') == 'user' else "مدل"
        p_role = document.add_paragraph()
        p_role.add_run(reshape_text(role) + ':').bold = True
        if msg.get('text'):
            p_text = document.add_paragraph(reshape_text(msg.get('text')))
            p_text.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if msg.get('images'):
            for img_url in msg.get('images'):
                try:
                    response = requests.get(img_url, stream=True, timeout=10)
                    response.raise_for_status()
                    image_stream = io.BytesIO(response.content)
                    document.add_picture(image_stream, width=Inches(4.0))
                except Exception as e:
                    print(f"Error fetching image {img_url}: {e}")
                    document.add_paragraph(reshape_text(f"[خطا در بارگذاری تصویر: {img_url}]"))
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

def create_txt_from_data(data):
    title = data.get('title', 'گفتگو')
    messages = data.get('messages', [])
    txt_parts = [f"عنوان: {title}\n{'='*20}\n"]
    for msg in messages:
        role = "کاربر" if msg.get('role') == 'user' else "مدل"
        txt_parts.append(f"{role}:")
        if msg.get('text'):
            txt_parts.append(msg.get('text'))
        if msg.get('images'):
            for img_url in msg.get('images'):
                txt_parts.append(f"[تصویر: {img_url}]")
        txt_parts.append("\n---\n")
    return io.BytesIO(("\n".join(txt_parts)).encode('utf-8'))

# --- توابع برای پردازش متن ساده ---
def create_file_from_string(text_content, file_format):
    if file_format == 'pdf':
        html = f"<!DOCTYPE html><html lang='fa'><head><meta charset='UTF-8'><style>@font-face {{ font-family: 'Vazir'; src: url('{FONT_FILE_NAME}'); }} body {{ font-family: 'Vazir', sans-serif; }}</style></head><body>{reshape_text(text_content).replace('\n', '<br>')}</body></html>"
        return io.BytesIO(HTML(string=html, base_url=BASE_DIR).write_pdf())
    elif file_format == 'docx':
        document = Document()
        document.add_paragraph(reshape_text(text_content))
        buffer = io.BytesIO()
        document.save(buffer)
        buffer.seek(0)
        return buffer
    else: # txt and html
        return io.BytesIO(text_content.encode('utf-8'))


# --- تابع پردازشگر اصلی درخواست ---
@app.route('/', methods=['POST', 'GET', 'HEAD'])
def process_request_route():
    if request.method != 'POST':
        return render_template('index.html') if request.method == 'GET' else ('', 200)

    file_format = request.form.get('format', 'txt').lower()
    json_content = request.form.get('json_content')
    text_content = request.form.get('content')
    
    mimetypes = {'pdf': 'application/pdf', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'html': 'text/html', 'txt': 'text/plain'}
    mimetype = mimetypes.get(file_format, 'text/plain')
    filename = f'export.{file_format}'
    buffer = None

    try:
        if json_content:
            data = json.loads(json_content)
            if file_format == 'pdf': buffer = create_pdf_from_data(data)
            elif file_format == 'docx': buffer = create_docx_from_data(data)
            elif file_format == 'html': buffer = io.BytesIO(create_html_from_data(data, is_for_pdf=False).encode('utf-8'))
            elif file_format == 'txt': buffer = create_txt_from_data(data)
        elif text_content:
            buffer = create_file_from_string(text_content, file_format)
        else:
            return "هیچ محتوایی برای تبدیل ارسال نشده است.", 400

        if buffer:
            return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)
        else:
            return "فرمت فایل نامعتبر است.", 400

    except Exception as e:
        traceback.print_exc()
        return f"یک خطای داخلی در سرور رخ داد: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
