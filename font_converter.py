# font_converter.py
import base64

# مطمئن شوید نام فایل فونت دقیق است
font_filename = 'Vazirmatn-Regular.ttf'
output_filename = 'font_base64.txt'

try:
    with open(font_filename, 'rb') as font_file:
        encoded_string = base64.b64encode(font_file.read()).decode('utf-8')
    
    with open(output_filename, 'w') as text_file:
        text_file.write(encoded_string)
        
    print(f"فونت با موفقیت به Base64 تبدیل شد و در فایل '{output_filename}' ذخیره شد.")
    print("محتوای این فایل را کپی کرده و در فایل app.py خود جای‌گذاری کنید.")

except FileNotFoundError:
    print(f"خطا: فایل فونت '{font_filename}' پیدا نشد. لطفاً آن را در همین پوشه قرار دهید.")
