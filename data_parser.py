#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduł odpowiedzialny za parsowanie danych programu z plików HTML lub LST.
"""

import os
import re
from bs4 import BeautifulSoup, Comment


class ProgramData:
    """
    Klasa reprezentująca dane programu.
    """

    def __init__(self, program_name="", material="", thickness=0,
                 program_time="", program_counts="", details_table_rows=None):
        self.program_name = program_name  # np. "mc2809"
        self.material = material  # np. "1.4301" – po przetworzeniu
        self.thickness = thickness  # np. 5.0 (mm)
        self.program_time = program_time  # np. "2.46 min"
        self.program_counts = program_counts  # np. "1"
        self.details_table_rows = details_table_rows or []  # lista – dla HTML: BS4 wierszy, dla LST: lista słowników


def parse_html_file(file_path):
    """
    Parsuje plik HTML i wyciąga z niego dane programu.
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

    # Jeśli grubość nie została wyznaczona – spróbuj wyszukać fragment zawierający "Blechdicke" lub "Blechmass Z"
    if thickness == 0:
        text_candidates = soup.find_all(string=re.compile(r"(Blechdicke|Blechmass Z)", re.IGNORECASE))
        for txt in text_candidates:
            m = re.search(r"(\d+(\.\d+)?)", txt)
            if m:
                thickness = float(m.group(1))
                break

    return ProgramData(program_name, material, thickness, program_time, program_counts, details_rows)


# ----- Funkcje pomocnicze do parsowania plików LST -----

def extract_lst_section(lines, begin_marker, end_marker):
    """
    Wyodrębnia linie z sekcji LST między begin_marker a end_marker.
    """
    in_section = False
    section_lines = []
    for line in lines:
        if begin_marker in line:
            in_section = True
            continue
        if end_marker in line:
            in_section = False
            break
        if in_section:
            section_lines.append(line.rstrip("\n"))
    return section_lines


def join_da_lines(lines):
    """
    Łączy linie DA z ich kontynuacjami (linie zaczynające się od "*").
    Zwraca listę pełnych linii DA.
    """
    da_lines = []
    current_line = ""
    for line in lines:
        if line.startswith("DA,"):
            if current_line:
                da_lines.append(current_line)
            current_line = line.strip()
        elif line.startswith("*"):
            current_line += " " + line.strip().lstrip("*").strip()
    if current_line:
        da_lines.append(current_line)
    return da_lines


def parse_lst_section_with_headers(section_lines):
    """
    Dla danej sekcji LST (z nagłówkami i danymi) wyodrębnia:
      - listę nagłówków (z linii zaczynających się od "MM,AT")
      - listę wierszy danych (każdy jako lista wartości pobranych z DA)
    """
    headers = []
    # Przetwarzamy część nagłówkową (MM,AT)
    for line in section_lines:
        if line.startswith("MM,AT"):
            match = re.search(r",\s*'([^']+)'", line)
            if match:
                header_name = match.group(1).strip()
                headers.append(header_name)
    # Przetwarzamy dane (DA)
    data_rows = []
    da_lines = join_da_lines(section_lines)
    for da in da_lines:
        parts = [p.strip(" '") for p in da.split(",") if p.strip()]
        if parts and parts[0] == "DA":
            data_rows.append(parts[1:])  # pomijamy pierwszy element "DA"
    return headers, data_rows


def parse_lst_file(file_path):
    """
    Parsuje plik LST i wyciąga z niego podstawowe dane programu oraz dane detali.
    W tym przykładzie:
      - Nazwa programu oraz czas trwania pobierane są z sekcji BEGIN_PROGRAMM.
      - Ilość powtórzeń oraz materiał – z BEGIN_EINRICHTEPLAN_INFO.
      - Grubość – z BEGIN_SHEET_TECH.
      - Detale – z BEGIN_PARTS_IN_PROGRAM (każdy wiersz zostanie przetworzony na słownik).
    """
    with open(file_path, "r", encoding="cp1250") as file:
        lines = file.readlines()

    # 1. Sekcja BEGIN_PROGRAMM – dane głównego programu
    prog_section = extract_lst_section(lines, "BEGIN_PROGRAMM", "ENDE_PROGRAMM")
    prog_headers, prog_data_rows = parse_lst_section_with_headers(prog_section)
    main_prog = None
    for row in prog_data_rows:
        if len(row) >= 2 and row[1].upper() == "HP":
            main_prog = row
            break
    if not main_prog and prog_data_rows:
        main_prog = prog_data_rows[-1]
    program_name = main_prog[0] if main_prog and len(main_prog) > 0 else ""
    program_time = (main_prog[3] + " min") if main_prog and len(main_prog) > 3 else "N/A"

    # 2. Sekcja BEGIN_EINRICHTEPLAN_INFO – pobieramy materiał oraz ilość powtórzeń
    einr_section = extract_lst_section(lines, "BEGIN_EINRICHTEPLAN_INFO", "ENDE_EINRICHTEPLAN_INFO")
    einr_headers, einr_data_rows = parse_lst_section_with_headers(einr_section)
    program_counts = "N/A"
    material = ""
    if einr_headers and einr_data_rows:
        data = einr_data_rows[0]  # zakładamy, że pierwszy wiersz zawiera dane
        if len(einr_headers) <= len(data):
            mapping = dict(zip(einr_headers, data))
            program_counts = mapping.get("Anzahl der Programmdurchlaeufe", "N/A")
            material_raw = mapping.get("Material-ID", "")
            # Dla LST chcemy, aby materiał był w formacie jak w HTML – czyli przed myślnikiem
            m = re.match(r"([^-]+)-\d+", material_raw)
            if m:
                material = m.group(1).strip()
            else:
                material = material_raw

    # 3. Sekcja BEGIN_SHEET_TECH – pobieramy grubość arkusza
    sht_section = extract_lst_section(lines, "BEGIN_SHEET_TECH", "ENDE_SHEET_TECH")
    sht_headers, sht_data_rows = parse_lst_section_with_headers(sht_section)
    thickness = 0
    if sht_headers and sht_data_rows:
        try:
            idx = sht_headers.index("Blechmass Z")
            data = sht_data_rows[0]
            if idx < len(data):
                thickness = float(data[idx])
        except (ValueError, IndexError):
            thickness = 0

    # 4. Sekcja BEGIN_PARTS_IN_PROGRAM – pobieramy dane detali jako listę słowników
    parts_section = extract_lst_section(lines, "BEGIN_PARTS_IN_PROGRAM", "ENDE_PARTS_IN_PROGRAM")
    parts_headers, parts_data_rows = parse_lst_section_with_headers(parts_section)
    details_table_rows = []
    if parts_headers and parts_data_rows:
        for row in parts_data_rows:
            mapping = dict(zip(parts_headers, row))
            details_table_rows.append(mapping)

    return ProgramData(program_name, material, thickness, program_time, program_counts, details_table_rows)


def get_program_data(file_path):
    """
    W zależności od rozszerzenia (HTML lub LST) wywołuje odpowiedni parser.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".html":
        return parse_html_file(file_path)
    elif ext == ".lst":
        return parse_lst_file(file_path)
    else:
        raise ValueError("Unsupported file type: " + ext)
