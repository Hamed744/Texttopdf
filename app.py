import os
import io
from flask import Flask, request, jsonify, send_file, render_template

# We don't need other libraries for this test
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)

# We only need the functions that are working
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

# --- Main request processing logic ---
def process_request(content, file_format):
    # --- THIS IS THE KEY CHANGE ---
    if file_format == 'pdf':
        # Instead of creating a PDF, we just send the existing dummy file
        try:
            # We are NOT creating anything, just sending a static file.
            return send_file(
                'dummy.pdf',
                as_attachment=True,
                download_name='test-static.pdf',
                mimetype='application/pdf'
            )
        except FileNotFoundError:
            # This will tell us if even the dummy.pdf is not found
            print("🔥🔥🔥 CRITICAL ERROR: dummy.pdf not found on the server!")
            return "File 'dummy.pdf' not found on server.", 500
            
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

# --- Flask routes (no changes needed) ---
@app.route('/convert', methods=['POST'])
def convert_text_api():
    # This route is for your chatbot, let's keep it simple for now
    return jsonify({"error": "API is in debug mode"}), 400

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            content = request.form.get('content', 'dummy content') # Use dummy content
            file_format = request.form.get('format', 'txt').lower()
            return process_request(content, file_format)
        except Exception as e:
            print(f"🔥🔥🔥 Web Form Error: {e}")
            return "Internal Server Error", 500
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
