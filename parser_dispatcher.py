"""
Moduł wybierający odpowiedni parser (HTML lub LST) na podstawie rozszerzenia pliku.
"""

import os
from html_parser import parse_html_file
from lst_parser import parse_lst_file
from program_data import ProgramData


def get_program_data(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".html":
        return parse_html_file(file_path)
    elif ext == ".lst":
        return parse_lst_file(file_path)
    else:
        raise ValueError("Unsupported file type: " + ext)
