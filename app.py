import os
import io
from flask import Flask, request, jsonify, send_file, render_template

# Import libraries for file generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# --- Final and Robust Font Loading ---
FONT_NAME = 'Vazir'
FONT_FILE_NAME = 'Vazirmatn-Regular.ttf'
FONT_LOADED_SUCCESSFULLY = False

# Get the absolute path to the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Create the full, absolute path to the font file
FONT_PATH = os.path.join(BASE_DIR, FONT_FILE_NAME)

try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        FONT_LOADED_SUCCESSFULLY = True
    # The print statements will appear in Render's Logs
except Exception as e:
    print(f"❌ ERROR LOADING FONT: {e}")


def create_pdf(text_content):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    font_to_use = FONT_NAME if FONT_LOADED_SUCCESSFULLY else 'Helvetica'
    p.setFont(font_to_use, 12)
    
    if FONT_LOADED_SUCCESSFULLY:
        p.setRTL()
        text_object = p.beginText()
        text_object.setTextOrigin(letter[0] - 100, letter[1] - 100)
    else:
        text_object = p.beginText()
        text_object.setTextOrigin(100, letter[1] - 100)
        
    text_object.setFont(font_to_use, 12)
    
    lines = text_content.split('\n')
    for line in lines:
        text_object.textLine(line)
        
    p.drawText(text_object)
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

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
    else:
        buffer = create_txt(content)
        filename = 'export.txt'
        mimetype = 'text/plain'

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )

@app.route('/convert', methods=['POST'])
def convert_text_api():
    try:
        data = request.json
        content = data.get('content')
        file_format = data.get('format', 'txt').lower()
        if not content:
            return jsonify({"error": "No content provided"}), 400
        return process_request(content, file_format)
    except Exception as e:
        print(f"🔥🔥🔥 API Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            content = request.form.get('content')
            file_format = request.form.get('format', 'txt').lower()
            if not content:
                return "لطفا متنی برای تبدیل وارد کنید.", 400
            return process_request(content, file_format)
        except Exception as e:
            print(f"🔥🔥🔥 Web Form Error: {e}")
            return "Internal Server Error", 500
    return render_template('index.html')

# --- NEW DEBUG ROUTE ---
@app.route('/debug')
def debug_info():
    info = []
    info.append("--- DEBUG INFORMATION ---")
    info.append(f"Current Working Directory: {os.getcwd()}")
    info.append(f"Base Directory (where app.py is): {BASE_DIR}")
    info.append(f"Full Font Path to check: {FONT_PATH}")

    if os.path.exists(FONT_PATH):
        info.append("✅ SUCCESS: Font file was found at the specified path.")
        if os.access(FONT_PATH, os.R_OK):
            info.append("✅ SUCCESS: Application has READ permission for the font file.")
        else:
            info.append("❌ ERROR: Font file exists but application does NOT have READ permission.")
    else:
        info.append("❌ ERROR: Font file was NOT found at the specified path.")
    
    info.append("\n--- Files in Base Directory ---")
    try:
        files_in_dir = os.listdir(BASE_DIR)
        if not files_in_dir:
            info.append("(Directory seems empty)")
        else:
            for f in files_in_dir:
                info.append(f)
    except Exception as e:
        info.append(f"Could not list directory contents: {e}")

    return f"<pre>{'<br>'.join(info)}</pre>"


if __name__ == '__main__':
    app.run(debug=True)
