"""
Moduł do parsowania plików LST z danymi programu.
"""

import os
import re
from program_data import ProgramData


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
    for line in section_lines:
        if line.startswith("MM,AT"):
            match = re.search(r",\s*'([^']+)'", line)
            if match:
                header_name = match.group(1).strip()
                headers.append(header_name)
    data_rows = []
    da_lines = join_da_lines(section_lines)
    for da in da_lines:
        parts = [p.strip(" '") for p in da.split(",") if p.strip()]
        if parts and parts[0] == "DA":
            data_rows.append(parts[1:])  # pomijamy pierwszy element "DA"
    return headers, data_rows


def convert_minutes_to_hhmmss(minutes_val):
    """
    Konwertuje wartość podaną w minutach (jako float) na format HH:MM:SS.
    """
    total_seconds = int(round(minutes_val * 60))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def parse_lst_file(file_path):
    """
    Parsuje plik LST i wyciąga z niego dane programu oraz dane detali.
    W szczególności:
      - Sekcja BEGIN_PROGRAMM: pobieramy nazwę programu oraz czas trwania (konwertowany na HH:MM:SS).
      - Sekcja BEGIN_EINRICHTEPLAN_INFO: pobieramy materiał (z pola "Material-ID") i ilość powtórzeń.
      - Sekcja BEGIN_SHEET_TECH: pobieramy grubość (z pola "Blechmass Z").
      - Sekcja BEGIN_PARTS_IN_PROGRAM: przekształcamy dane detali do listy słowników.
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
    # Konwersja czasu z minut (np. "2.46") na format HH:MM:SS
    if main_prog and len(main_prog) > 3:
        try:
            minutes_val = float(main_prog[3])
            program_time = convert_minutes_to_hhmmss(minutes_val)
        except Exception:
            program_time = "N/A"
    else:
        program_time = "N/A"

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


# def get_program_data(file_path):
#     """
#     W zależności od rozszerzenia (HTML lub LST) wywołuje odpowiedni parser.
#     """
#     ext = os.path.splitext(file_path)[1].lower()
#     if ext == ".html":
#         from html_parser import parse_html_file
#         return parse_html_file(file_path)
#     elif ext == ".lst":
#         return parse_lst_file(file_path)
#     else:
#         raise ValueError("Unsupported file type: " + ext)
