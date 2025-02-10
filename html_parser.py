"""
Moduł do parsowania plików HTML z danymi programu.
"""

import os
import re
from bs4 import BeautifulSoup, Comment
from program_data import ProgramData


def format_time_string(time_str):
    """
    Przyjmuje ciąg znaków reprezentujący czas, np. "8 : 05 : 30" lub "8:5:3",
    usuwa spacje i uzupełnia zerami poszczególne części do dwóch cyfr, zwracając
    wynik w formacie HH:MM:SS.
    """
    # Usuń wszystkie spacje
    time_str = time_str.replace(" ", "")
    parts = time_str.split(":")
    if len(parts) == 3:
        hour, minute, second = parts
        hour = hour.zfill(2)
        minute = minute.zfill(2)
        second = second.zfill(2)
        return f"{hour}:{minute}:{second}"
    return time_str


def parse_html_file(file_path):
    """
    Parsuje plik HTML i wyciąga z niego dane programu oraz detali.
    Dodatkowo próbuje wyłuskać grubość materiału oraz liczbę powtórzeń.
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
                    # Pobieramy część przed nawiasem, jeśli występuje
                    program_time = text.split("[")[0].strip() if "[" in text else text
        # Zmieniona logika pobierania liczby powtórzeń
        elif ("program" in c_text.lower() and "durch" in c_text.lower()):
            tr = comment.find_next_sibling("tr")
            if tr:
                td_tags = tr.find_all("td")
                for td in td_tags:
                    txt = td.get_text(strip=True)
                    if txt.isdigit():
                        program_counts = txt
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

    # Ujednolicenie formatu czasu do HH:MM:SS
    program_time = format_time_string(program_time)

    return ProgramData(program_name, material, thickness, program_time, program_counts, details_rows)
