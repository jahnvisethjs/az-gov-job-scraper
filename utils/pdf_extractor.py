"""
PDF and DOCX resume extraction utilities.
Converts resume files to plain text for AI processing.
"""
import io
from typing import Optional
import PyPDF2
import pdfplumber
from docx import Document


class ResumeExtractor:
    """Extract text from resume files (PDF, DOCX)"""
    
    @staticmethod
    def extract_from_pdf(file_bytes: bytes) -> str:
        """
        Extract text from PDF using multiple methods.
        
        Args:
            file_bytes: PDF file as bytes
            
        Returns:
            Extracted text string
        """
        text = ""
        
        # Try pdfplumber first (better for formatted PDFs)
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber failed: {e}, falling back to PyPDF2")
        
        # Fallback to PyPDF2 if pdfplumber didn't work
        if not text.strip():
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            except Exception as e:
                print(f"PyPDF2 also failed: {e}")
                raise ValueError("Could not extract text from PDF")
        
        return text.strip()
    
    @staticmethod
    def extract_from_docx(file_bytes: bytes) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_bytes: DOCX file as bytes
            
        Returns:
            Extracted text string
        """
        try:
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise ValueError(f"Could not extract text from DOCX: {e}")
    
    @staticmethod
    def extract_from_txt(file_bytes: bytes) -> str:
        """Extract text from plain text file."""
        try:
            return file_bytes.decode('utf-8').strip()
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252']:
                try:
                    return file_bytes.decode(encoding).strip()
                except:
                    continue
            raise ValueError("Could not decode text file")
    
    @classmethod
    def extract_text(cls, file_bytes: bytes, filename: str) -> str:
        """
        Extract text from resume file based on extension.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename with extension
            
        Returns:
            Extracted text
            
        Raises:
            ValueError: If file format is unsupported or extraction fails
        """
        extension = filename.lower().split('.')[-1]
        
        if extension == 'pdf':
            return cls.extract_from_pdf(file_bytes)
        elif extension == 'docx':
            return cls.extract_from_docx(file_bytes)
        elif extension == 'txt':
            return cls.extract_from_txt(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: {extension}")


def validate_resume_size(file_bytes: bytes, max_mb: int = 5) -> bool:
    """
    Check if resume file size is within limits.
    
    Args:
        file_bytes: File content as bytes
        max_mb: Maximum allowed size in MB
        
    Returns:
        True if valid, False otherwise
    """
    size_mb = len(file_bytes) / (1024 * 1024)
    return size_mb <= max_mb
