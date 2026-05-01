import pytesseract
from PIL import Image
import os

def extract_text(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='ara+eng+fra')
        
        if not text or text.strip() == "":
            from PIL import ImageEnhance
            img = img.convert('L')
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            text = pytesseract.image_to_string(img, lang='ara+eng+fra')
        
        if not text or text.strip() == "":
            return "No text found in image"
        
        return text.strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return "Error processing image"
    
#========================================================================
"""import pytesseract
from PIL import Image
import os

def extract_text(image_path):
    try:
        # التحقق من وجود الملف
        if not os.path.exists(image_path):
            return "Image file not found"
        
        # فتح الصورة
        img = Image.open(image_path)
        
        # تحويل الصورة لأبيض وأسود (يحسن القراءة)
        img = img.convert('L')
        
        # استخراج النص بالإنجليزية أولاً
        text = pytesseract.image_to_string(img, lang='eng')
        
        # إذا كان النص فارغاً، جرب العربية والإنجليزية
        if not text or text.strip() == "":
            text = pytesseract.image_to_string(img, lang='ara+eng')
        
        # إذا كان النص فارغاً، جرب بدون تحديد لغة
        if not text or text.strip() == "":
            text = pytesseract.image_to_string(img)
        
        return text.strip() if text.strip() else "No text found in image"
        
    except Exception as e:
        return f"OCR Error: {str(e)}" """