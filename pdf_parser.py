# pdf_parser.py
import fitz  # PyMuPDF
from models import Program, Detail
import old_pdf_file_parser
import new_pdf_file_parser
from pdf_utils import *  # Import funkcji pomocniczych

def parse_pdf(file_path: str) -> Program:
    """
    Parsuje plik PDF – automatycznie wykrywa, czy jest to stary czy nowy format,
    i wywołuje odpowiednią logikę parsowania.
    """
    doc = fitz.open(file_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text")

    # Jeśli w tekście występuje fraza charakterystyczna dla nowego formatu, np. "Plan konfiguracji:",
    # wywołujemy funkcję obsługującą nowy typ pliku.
    if "Plan konfiguracji:" in full_text:
        program = new_pdf_file_parser.parse_pdf_new(doc, full_text)
    else:
        program = old_pdf_file_parser.parse_pdf_old(doc, full_text)

    doc.close()
    return program
