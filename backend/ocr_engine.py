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
    
