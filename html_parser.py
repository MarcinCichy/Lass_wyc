"""
Moduł do parsowania plików HTML z danymi programu.
"""

import os
import re
from bs4 import BeautifulSoup, Comment
from program_data import ProgramData


def parse_html_file(file_path):
    """
    Parsuje plik HTML i wyciąga z niego dane programu oraz detali.
    Dodatkowo próbuje wyłuskać grubość materiału.
    """
    with open(file_path, "r", encoding="cp1250") as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "html.parser")
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    program_name = ""
    material = ""
    thickness = 0
    program_time = ""
    program_counts = ""
    details_rows = []

    for comment in comments:
        c_text = comment.strip()
        if c_text == "Programm-Nummer und Bemerkung":
            tr = comment.find_next_sibling("tr")
            if tr:
                b_tag = tr.find("b")
                if b_tag:
                    program_name = b_tag.get_text(strip=True)
        elif c_text == "Material (Technologietabelle)":
            tr = comment.find_next_sibling("tr")
            if tr:
                b_tag = tr.find("b")
                if b_tag:
                    full_text = b_tag.get_text(strip=True)
                    # Zakładamy format "MaterialID-Grubość", np. "1.4301-50"
                    m = re.match(r"([^-]+)-(\d+)", full_text)
                    if m:
                        material = m.group(1).strip()
                        try:
                            thickness = abs(int(m.group(2)) / 10)
                        except ValueError:
                            thickness = 0
                    else:
                        material = full_text
        elif c_text == "Maschinenzeit/Tafel":
            tr = comment.find_next_sibling("tr")
            if tr:
                nobr_tag = tr.find("nobr")
                if nobr_tag:
                    text = nobr_tag.get_text(strip=True)
                    program_time = text.split("[")[0].strip() if "[" in text else text
        elif c_text == "Anzahl Programmdurchlaeufe":
            tr = comment.find_next("tr")
            if tr:
                td_tags = tr.find_all("td")
                for td in td_tags:
                    if td.get_text(strip=True).isdigit():
                        program_counts = td.get_text(strip=True)
                        break
        elif c_text == "HTML-Block: Einzelteil-Informationen mit Grafiken, ohne Barcode":
            table = comment.find_next("table")
            if table:
                details_rows = table.find_all("tr")

    # Jeśli grubość nadal wynosi 0, spróbuj dodatkowo wyszukać fragmenty zawierające "Blechdicke" lub "Blechmass Z"
    if thickness == 0:
        text_candidates = soup.find_all(string=re.compile(r"(Blechdicke|Blechmass Z)", re.IGNORECASE))
        for txt in text_candidates:
            m = re.search(r"(\d+(\.\d+)?)", txt)
            if m:
                thickness = float(m.group(1))
                break

    return ProgramData(program_name, material, thickness, program_time, program_counts, details_rows)
