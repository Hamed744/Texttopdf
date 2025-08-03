import os
import io
from flask import Flask, request, send_file, render_template

app = Flask(__name__)

# --- Plain Text (.txt) Generation ---
def create_txt(text_content):
    # This is a very simple function with no external dependencies
    buffer = io.BytesIO(text_content.encode('utf-8'))
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        file_format = request.form.get('format', 'txt').lower() # We'll ignore the format for now
        
        if not content:
            return "لطفا متنی برای تبدیل وارد کنید.", 400
        
        try:
            # We only create .txt for this test
            buffer = create_txt(content)
            filename = 'test-export.txt'
            mimetype = 'text/plain'

            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )
        except Exception as e:
            # If even this fails, we can see the error in the logs
            print(f"🔥🔥🔥 UNEXPECTED ERROR IN TXT CREATION: {e}")
            return "یک خطای بسیار غیرمنتظره رخ داد.", 500

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
