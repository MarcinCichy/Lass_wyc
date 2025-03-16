import re
from models import Program, Detail
from pdf_utils import find_field, find_in_section, extract_all_detail_images


def parse_detail_section(section_text: str) -> Detail:
    """
    Parsuje pojedynczy blok zawierający informacje o detalu.
    Oczekujemy, że w danym bloku pojawią się etykiety:
      - "Plik geo:" – nazwa detalu,
      - "Wymiary:" – wymiary detalu (np. "60,00 x 78,00 mm"),
      - "Szt.:" – ilość detalu,
      - "Czas obróbki detalu:" – czas cięcia w formacie HH:MM:SS (konwertowany na sekundy).
    Jeśli etykiety nie występują, używamy domyślnych wartości.
    """
    section_text = section_text.strip()

    # Nazwa detalu
    det_name_match = re.search(r"Plik\s*geo:\s*(.+)", section_text, re.IGNORECASE)
    det_name = det_name_match.group(1).strip() if det_name_match else ""

    # Wymiary
    dims_match = re.search(r"Wymiary:\s*(.+)", section_text, re.IGNORECASE)
    dims_str = dims_match.group(1).strip() if dims_match else ""
    if "x" in dims_str:
        dims_parts = dims_str.split("x")
        dim_x = dims_parts[0].strip()
        # Przyjmujemy, że wymiar Y to pierwszy token drugiej części
        dim_y = dims_parts[1].strip().split()[0]
    else:
        dim_x = dims_str
        dim_y = ""

    # Ilość – etykieta "Szt.:"
    qty_match = re.search(r"Szt\.:\s*(\d+)", section_text, re.IGNORECASE)
    try:
        quantity = int(qty_match.group(1).strip()) if qty_match else 1
    except Exception:
        quantity = 1

    # Czas obróbki – etykieta "Czas obróbki detalu:" w formacie HH:MM:SS, konwertowany na sekundy
    time_match = re.search(r"Czas\s*obróbki\s*detalu:\s*([\d:]+)", section_text, re.IGNORECASE)
    if time_match:
        time_str = time_match.group(1).strip()
        try:
            h, m, s = time_str.split(":")
            cut_time = int(h) * 3600 + int(m) * 60 + int(s)
        except Exception:
            cut_time = 0
    else:
        cut_time = 0

    return Detail(
        name=det_name,
        quantity=quantity,
        dimensions=dims_str,  # lub f"{dim_x} x {dim_y}"
        cut_time=cut_time,
        cut_length=0.0,
        weight=0.0,
        image_path=None
    )


def parse_pdf_new(doc, full_text: str) -> Program:
    try:
        # Łączymy tekst ze wszystkich stron przy użyciu get_text("dict")
        combined_text = ""
        for page in doc:
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            combined_text += span["text"] + " "
                        combined_text += "\n"
                elif "text" in block:
                    combined_text += block["text"] + "\n"

        # --- Dane programu (jak wcześniej)
        prog_name_match = re.search(r"Liczba detali:\s*Liczba arkuszy:\s*\n\s*(\S+)", combined_text,
                                    re.IGNORECASE | re.MULTILINE)
        program_name = prog_name_match.group(1).strip() if prog_name_match else ""

        rep_match = re.search(r"Czas\s+trwania\s*\n\s*(\S+)\s+(\d+)", combined_text, re.IGNORECASE | re.MULTILINE)
        program_counts = int(rep_match.group(2)) if rep_match else 0

        material_match = re.search(r"[A-Z0-9]+----[0-9x]+\s*\((\d+\.\d+)\)", combined_text, re.IGNORECASE)
        material = material_match.group(1).strip() if material_match else ""

        wymiary_pos = combined_text.find("Wymiary:")
        if wymiary_pos != -1:
            try:
                substring = combined_text[wymiary_pos:].splitlines()[12]
                tokens = substring.split()
                thick_str = tokens[-2].replace(",", ".")
                thicknes = abs(float(thick_str))
            except Exception:
                thicknes = 0.0
        else:
            thicknes = 0.0

        machine_time = find_field(combined_text, "Czas trwania")
        machine_time = re.sub(r"\s*\[.*\]", "", machine_time).strip()

        print("Nowy PDF:")
        print("1. Nazwa programu:", program_name)
        print("2. Rodzaj materiału (z nawiasu):", material)
        print("3. Czas trwania:", machine_time)
        print("4. Ilość powtórzeń programu:", program_counts)
        print("5. GRUBOŚĆ:", thicknes)

        # --- Parsowanie sekcji detali
        # Wyodrębniamy blok detali – ograniczamy go od "Informacja o pojedynczych detalach/zleceniu"
        # do "Zlecenia wykonania" (bo dalszy tekst nie dotyczy detali)
        if "Informacja o pojedynczych detalach/zleceniu" in combined_text:
            detail_block = combined_text.split("Informacja o pojedynczych detalach/zleceniu", 1)[1].strip()
            if "Zlecenia wykonania" in detail_block:
                detail_block = detail_block.split("Zlecenia wykonania", 1)[0].strip()
        else:
            detail_block = ""

        print("Detail block (wycięty):")
        print(detail_block)

        # Dzielenie bloku detali – zakładamy, że każdy detal zaczyna się od linii, która (opcjonalnie)
        # zaczyna się od "#" i zawiera "Nr czesci:" lub "Nr części:".
        # Używamy wzorca, który dopasowuje początek linii (opcjonalne "#") oraz frazę.
        detail_sections = re.split(r"(?im)^(?:#\s*)?Nr\s*(?:czesci|części):", detail_block)
        # Pierwszy element może być pusty lub zawierać nagłówki – pomijamy go, jeśli jest pusty.
        detail_sections = [sec.strip() for sec in detail_sections if sec.strip()]
        print("Found", len(detail_sections), "detail sections")

        details = []
        for sec in detail_sections:
            # Jeśli w sekcji występuje oczekiwana etykieta, np. "Plik geo:" – uznajemy to za sekcję detalu
            if "Plik geo:" in sec:
                det = parse_detail_section(sec)
                details.append(det)

        # Przypisujemy obrazy do detali, jeśli są dostępne
        images = extract_all_detail_images(doc)
        for i, det in enumerate(details):
            if i < len(images):
                det.image_path = images[i]

        prog = Program(
            name=program_name,
            material=material,
            thicknes=thicknes,
            machine_time=machine_time,
            program_counts=program_counts,
            details=details
        )
        print("Program (nowy PDF):", prog)
        return prog

    except Exception as e:
        print("Wystąpił błąd w parse_pdf_new:", e)
        return Program(name="", material="", thicknes=0.0, machine_time="", program_counts=0, details=[])
