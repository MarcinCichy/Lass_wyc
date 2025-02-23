"""
Moduł do parsowania plików PDF z danymi programu przy użyciu biblioteki PyMuPDF (fitz).
Wymagany: pip install PyMuPDF
"""

import re
import fitz  # PyMuPDF
from program_data import ProgramData
import os

def format_time_string(time_str):
    """
    Przyjmuje ciąg znaków reprezentujący czas, np. "0 : 00 : 07" lub "0:0:7",
    usuwa spacje i uzupełnia poszczególne części zerami do dwóch cyfr,
    zwracając wynik w formacie HH:MM:SS.
    """
    print("[DEBUG] format_time_string: input =", time_str)
    time_str = time_str.replace(" ", "")
    parts = time_str.split(":")
    if len(parts) == 3:
        hour, minute, second = parts
        formatted = f"{hour.zfill(2)}:{minute.zfill(2)}:{second.zfill(2)}"
        print("[DEBUG] format_time_string: formatted =", formatted)
        return formatted
    print("[DEBUG] format_time_string: returning original string =", time_str)
    return time_str

def parse_pdf_file(file_path):
    """
    Parsuje plik PDF i wyciąga dane programu oraz informacje o detalu.

    Wyszukiwane dane:
      - Program Name: linie zaczynające się od "NAZWA PROGRAMU:", "NAZWA ZLECENIA:" lub "Program glówny:"
      - Material oraz Thickness: linia zawierająca "MATERIAŁ" (np. "MATERIAŁ (ARKUSZ):" lub "MATERIAŁ (TT):")
        – oczekujemy formatu np. "St37-30"
      - Program Time: linia zaczynająca się od "CZAS MASZYNOWY:" lub "CZAS TRWANIA:" – pobierana część przed nawiasem
      - Program Counts: linia zaczynająca się od "ILOŚĆ PRZEBIEGÓW PROGRAMU:"
      - Details Rows: blok tekstu zaczynający się od "INFORMACJA O DETALU" lub "Detale", aż do napotkania pustej linii.

    Zwraca obiekt ProgramData.
    """
    print("[DEBUG] Starting parse_pdf_file for:", file_path)
    try:
        doc = fitz.open(file_path)
        print("[DEBUG] PDF opened successfully. Number of pages:", doc.page_count)
    except Exception as e:
        print("[ERROR] Failed to open PDF:", e)
        return None

    text = ""
    for page_num, page in enumerate(doc, start=1):
        try:
            page_text = page.get_text("text")
            print(f"[DEBUG] Extracted text from page {page_num}, length:", len(page_text))
            text += page_text + "\n"
        except Exception as e:
            print(f"[ERROR] Failed to extract text from page {page_num}:", e)
            continue
    doc.close()
    print("[DEBUG] Finished extracting text from all pages.")

    lines = text.splitlines()
    print("[DEBUG] Total number of lines extracted:", len(lines))

    program_name = ""
    material = ""
    thickness = 0
    program_time = ""
    program_counts = ""
    details_rows = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        print("[DEBUG] Processing line:", line)
        # Szukamy nazwy programu – sprawdzamy różne warianty
        if line.startswith("NAZWA PROGRAMU:"):
            content = line.split(":", 1)[1].strip()
            if not content and i+1 < len(lines):
                i += 1
                content = lines[i].strip()
            program_name = content
            print("[DEBUG] Found program name (NAZWA PROGRAMU):", program_name)
        elif line.startswith("NAZWA ZLECENIA:") and not program_name:
            content = line.split(":", 1)[1].strip()
            if not content and i+1 < len(lines):
                i += 1
                content = lines[i].strip()
            program_name = content
            print("[DEBUG] Found program name (NAZWA ZLECENIA):", program_name)
        elif line.startswith("Program glówny:") and not program_name:
            content = line.split(":", 1)[1].strip()
            if not content and i+1 < len(lines):
                i += 1
                content = lines[i].strip()
            program_name = content
            print("[DEBUG] Found program name (Program glówny):", program_name)
        # Szukamy materiału – linia zawiera słowo "MATERIAŁ" oraz dwukropek
        elif "MATERIAŁ" in line and ":" in line:
            content = line.split(":", 1)[1].strip()
            if not content and i+1 < len(lines):
                i += 1
                content = lines[i].strip()
            print("[DEBUG] Found material line:", content)
            m = re.search(r"([^-]+)-(\d+)", content)
            if m:
                material = m.group(1).strip()
                try:
                    thickness = abs(int(m.group(2)) / 10)
                    print("[DEBUG] Parsed material:", material, "Thickness:", thickness)
                except ValueError:
                    thickness = 0
                    print("[DEBUG] ValueError when parsing thickness.")
            else:
                material = content
                print("[DEBUG] No regex match for material; material set to:", material)
        # Szukamy czasu – linia zaczynająca się od "CZAS MASZYNOWY:" lub "CZAS TRWANIA:"
        elif line.startswith("CZAS MASZYNOWY:") or line.startswith("CZAS TRWANIA:"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                time_part = parts[1].split("[")[0].strip()
                if not time_part and i+1 < len(lines):
                    i += 1
                    time_part = lines[i].strip()
                program_time = format_time_string(time_part)
                print("[DEBUG] Found program time:", program_time)
        # Szukamy ilości przebiegów
        elif line.startswith("ILOŚĆ PRZEBIEGÓW PROGRAMU:"):
            content = line.split(":", 1)[1].strip()
            if not content and i+1 < len(lines):
                i += 1
                content = lines[i].strip()
            program_counts = content
            print("[DEBUG] Found program counts:", program_counts)
        # Szukamy bloku detali – gdy linia zawiera "INFORMACJA O DETALU" lub zaczyna się od "Detale"
        elif "INFORMACJA O DETALU" in line or line.startswith("Detale"):
            details_rows = []
            print("[DEBUG] Found detail block marker:", line)
            j = i
            while j < len(lines):
                detail_line = lines[j].strip()
                if detail_line == "":
                    break
                details_rows.append(detail_line)
                j += 1
            print("[DEBUG] Collected details rows, count:", len(details_rows))
            i = j - 1  # aktualizacja indeksu
        i += 1

    if not program_name:
        program_name = os.path.basename(file_path)
        print("[DEBUG] Program name not found; using filename:", program_name)

    print("[DEBUG] Parsing complete. Program Name:", program_name)
    return ProgramData(program_name, material, thickness, program_time, program_counts, details_rows)

if __name__ == "__main__":
    pdf_file = "anmar test stary_1.pdf"  # lub inny plik PDF
    program_data = parse_pdf_file(pdf_file)
    if program_data:
        print("Program Name:", program_data.program_name)
        print("Material:", program_data.material)
        print("Thickness:", program_data.thickness)
        print("Program Time:", program_data.program_time)
        print("Program Counts:", program_data.program_counts)
        print("Details Rows:")
        for row in program_data.details_rows:
            print(row)
    else:
        print("Nie udało się przetworzyć pliku PDF.")
