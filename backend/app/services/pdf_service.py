"""
Service to extract text from PDF files and identify variables
"""
import re
from typing import List, Dict, Optional
from pathlib import Path

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    try:
        import pdfplumber
        PDF_SUPPORT = True
        USE_PDFPLUMBER = True
    except ImportError:
        PDF_SUPPORT = False
        USE_PDFPLUMBER = False

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    Returns the extracted text as a string.
    """
    if not PDF_SUPPORT:
        raise ImportError("PDF processing library not installed. Install PyPDF2 or pdfplumber.")
    
    text = ""
    
    try:
        if USE_PDFPLUMBER:
            # Use pdfplumber (better text extraction)
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        else:
            # Use PyPDF2 (fallback)
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    return text.strip()

def identify_variables(text: str) -> List[str]:
    """
    Identify variables in the text.
    Variables should be in the format {{variable_name}} or {{variable.name}}.
    Returns a list of unique variable names found.
    """
    # Pattern to match {{variable_name}} or {{variable.name}}
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, text)
    
    # Remove duplicates and return unique variable names
    unique_variables = list(set(matches))
    return sorted(unique_variables)

def replace_variables(text: str, variables: Dict[str, str]) -> str:
    """
    Replace variables in text with actual values.
    Variables in format {{variable_name}} will be replaced with values from the dictionary.
    
    Args:
        text: Text with variables in {{variable_name}} format
        variables: Dictionary mapping variable names to their values
    
    Returns:
        Text with all variables replaced
    """
    result = text
    
    for var_name, var_value in variables.items():
        # Replace {{variable_name}} with the value
        pattern = r'\{\{' + re.escape(var_name) + r'\}\}'
        result = re.sub(pattern, str(var_value), result)
    
    return result

