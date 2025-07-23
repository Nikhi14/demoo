import PyPDF2
import io
from docx import Document
import fitz  # PyMuPDF for better PDF processing

class FileProcessor:
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, file):
        """Extract text from PDF file using PyMuPDF for better accuracy"""
        try:
            # Read file content
            file_content = file.read()
            
            # Use PyMuPDF for better text extraction
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            text = ""
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text += page.get_text()
            
            pdf_document.close()
            return text.strip()
            
        except Exception as e:
            # Fallback to PyPDF2
            try:
                file.seek(0)  # Reset file pointer
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text.strip()
            except Exception as fallback_error:
                raise Exception(f"Failed to extract PDF text: {str(e)}, Fallback error: {str(fallback_error)}")
    
    def extract_text_from_docx(self, file):
        """Extract text from DOCX file"""
        try:
            doc = Document(file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract DOCX text: {str(e)}")
    
    def extract_text_from_txt(self, file):
        """Extract text from TXT file"""
        try:
            return file.read().decode('utf-8').strip()
        except Exception as e:
            raise Exception(f"Failed to extract TXT text: {str(e)}")
