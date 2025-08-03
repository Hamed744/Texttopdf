import os
import io
from flask import Flask, request, send_file, render_template
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# --- PDF Generation (Simple, no custom font) ---
def create_pdf(text_content):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont('Helvetica', 12) # Using a built-in font
    
    text_object = p.beginText()
    text_object.setTextOrigin(100, 750) # LTR origin
    text_object.setFont('Helvetica', 12)
    
    lines = text_content.split('\n')
    for line in lines:
        text_object.textLine(line)
        
    p.drawText(text_object)
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            return "لطفا متنی برای تبدیل وارد کنید.", 400
        
        try:
            buffer = create_pdf(content)
            filename = 'test-pdf-export.pdf'
            mimetype = 'application/pdf'

            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )
        except Exception as e:
            print(f"🔥🔥🔥 UNEXPECTED ERROR IN PDF CREATION: {e}")
            return "خطا در ساخت PDF.", 500

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
