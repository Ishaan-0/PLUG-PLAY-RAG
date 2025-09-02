from pdf2image import convert_from_path
import pytesseract as pt 

class CustomPDFProcessor:
    def __init__(self, file_path):
        self.file_path = file_path 
    
    def extract_text(self):
        all_text = ""
        pdf_image = convert_from_path(self.file_path)
        for idx, page in enumerate(pdf_image):
            text = pt.image_to_string(page)
            all_text += text + "\n"
        return all_text