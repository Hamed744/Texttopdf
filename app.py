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

# --- PDF Generation with Persian Support ---
FONT_NAME = 'Vazir'
FONT_FILE = 'Vazirmatn-Regular.ttf'
FONT_LOADED_SUCCESSFULLY = False

try:
    # Check if the file exists in the current directory
    if os.path.exists(FONT_FILE):
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
        FONT_LOADED_SUCCESSFULLY = True
        print(f"✅ فونت '{FONT_NAME}' با موفقیت بارگذاری شد.")
    else:
        # This will be printed in Render's logs if the font file is missing
        print(f"⚠️ هشدار: فایل فونت '{FONT_FILE}' در مسیر پروژه یافت نشد.")
except Exception as e:
    # This will be printed if there's an error loading the font
    print(f"❌ خطا در بارگذاری فونت '{FONT_FILE}': {e}")


def create_pdf(text_content):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Use the Persian font only if it was loaded successfully
    if FONT_LOADED_SUCCESSFULLY:
        p.setFont(FONT_NAME, 12)
        p.setRTL()
        text_object = p.beginText()
        text_object.setTextOrigin(letter[0] - 100, letter[1] - 100)
        text_object.setFont(FONT_NAME, 12)
    else:
        # Fallback to a default LTR English font
        p.setFont('Helvetica', 12)
        text_object = p.beginText()
        text_object.setTextOrigin(100, letter[1] - 100)
        text_object.setFont('Helvetica', 12)

    lines = text_content.split('\n')
    for line in lines:
        text_object.textLine(line)
        
    p.drawText(text_object)
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# ... (The rest of the functions: create_docx, create_txt, create_xlsx remain the same) ...
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

# API Endpoint for your chatbot
@app.route('/convert', methods=['POST'])
def convert_text_api():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
            
        content = data.get('content')
        file_format = data.get('format', 'txt').lower()

        if not content:
            return jsonify({"error": "No content provided"}), 400

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
        else: # Default to txt
            buffer = create_txt(content)
            filename = 'export.txt'
            mimetype = 'text/plain'

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
    except Exception as e:
        # Log the actual error to Render's logs for debugging
        print(f"🔥🔥🔥 An unexpected error occurred: {e}")
        # Return a generic error to the user
        return jsonify({"error": "An internal error occurred on the server."}), 500


# Web page for manual conversion
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # This will now be handled by the API function to ensure errors are caught
        return convert_text_api()

    return render_template('index.html')


if __name__ == '__main__':
    # For local development
    app.run(debug=True)
