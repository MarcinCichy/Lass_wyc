import re
from models import Program, Detail
from pdf_utils import find_field, find_in_section, extract_all_detail_images
from utils import copy_image_to_static


def parse_detail_section(section_text: str) -> Detail:
    """
    Parsuje blok tekstu z informacjami o detalu.

    Próbuje wyłuskać pełną nazwę detalu (wraz ze spacjami) na podstawie
    fragmentu tekstu po etykiecie "Plik geo:" - oczekujemy wzorca, że
    nazwa będzie miała postać "coś .geo". Usuwamy końcówkę ".geo",
    a pozostałą część przyjmujemy jako nazwę detalu.

    Dodatkowo wyodrębnia:
      - wymiary (np. "60,00 x 78,00 mm"),
      - ilość (Szt.:) – pierwszą liczbę po etykiecie "Szt.:",
      - czas obróbki w formacie HH:MM:SS, konwertowany na sekundy.
    Jeśli którejś wartości nie znajdzie, ustawia wartość domyślną.
    """
    text = section_text.strip()

    # Szukamy fragmentu zaczynającego się od "Plik geo:" i kończącego na ".geo"
    det_name = ""
    match = re.search(r'Plik\s+geo:\s*(.+?\.geo)', text, re.IGNORECASE)
    if match:
        full_name = match.group(1).strip()
        # Usuń końcówkę ".geo"
        if full_name.lower().endswith(".geo"):
            det_name = full_name[:-4].strip()
        else:
            det_name = full_name
    # Jeśli nie znaleziono, można spróbować innego podejścia, np. przeszukać wszystkie dopasowania
    if not det_name:
        geo_matches = re.findall(r'([^\n]+?\.geo)', text, re.IGNORECASE)
        if geo_matches:
            # Przyjmujemy ostatni dopasowany ciąg
            full_name = geo_matches[-1].strip()
            if full_name.lower().endswith(".geo"):
                det_name = full_name[:-4].strip()
            else:
                det_name = full_name

    # Wyodrębniamy wymiary – np. "60,00 x 78,00 mm"
    dims_match = re.search(r'(\d+,\d+\s*x\s*\d+,\d+\s*mm)', text, re.IGNORECASE)
    dimensions = dims_match.group(1).strip() if dims_match else ""

    # Wyodrębniamy ilość – szukamy liczby po etykiecie "Szt.:"
    qty_match = re.search(r'Szt\.:\s*(\d+)', text, re.IGNORECASE)
    if not qty_match:
        qty_match = re.search(r'^\s*(\d+)\s*$', text, re.MULTILINE)
    try:
        quantity = int(qty_match.group(1).strip()) if qty_match else 1
    except Exception:
        quantity = 1

    # Wyodrębniamy czas obróbki – format HH:MM:SS
    time_match = re.search(r'(\d{2}:\d{2}:\d{2})', text)
    cut_time = 0
    if time_match:
        time_str = time_match.group(1)
        try:
            h, m, s = time_str.split(":")
            cut_time = int(h) * 3600 + int(m) * 60 + int(s)
        except Exception:
            cut_time = 0

    return Detail(
        name=det_name,
        quantity=quantity,
        dimensions=dimensions,
        cut_time=cut_time,
        cut_length=0.0,
        weight=0.0,
        image_path=None
    )


def parse_pdf_new(doc, full_text: str) -> Program:
    try:
        # Łączymy tekst ze wszystkich stron korzystając z get_text("dict")
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

        # --- Dane programu:
        prog_name_match = re.search(r"Liczba detali:\s*Liczba arkuszy:\s*\n\s*(\S+)", combined_text,
                                    re.IGNORECASE | re.MULTILINE)
        program_name = prog_name_match.group(1).strip() if prog_name_match else ""

        rep_match = re.search(r"Czas\s+trwania\s*\n\s*(\S+)\s+(\d+)", combined_text,
                              re.IGNORECASE | re.MULTILINE)
        program_counts = int(rep_match.group(2)) if rep_match else 0

        material_match = re.search(r"[A-Z0-9]+----[0-9x]+\s*\((\d+\.\d+)\)", combined_text,
                                   re.IGNORECASE)
        material = material_match.group(1).strip() if material_match else ""

        # Grubość materiału – wyodrębniamy z ciągu w formacie "X x Y x Z mm"
        dimensions_regex = r'(\d+,\d+)\s*x\s*(\d+,\d+)\s*x\s*(\d+,\d+)\s*mm'
        dim_match = re.search(dimensions_regex, combined_text, re.IGNORECASE)
        if dim_match:
            thick_str = dim_match.group(3).replace(",", ".")
            try:
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

        # --- Parsowanie sekcji detali:
        if "Informacja o pojedynczych detalach/zleceniu" in combined_text:
            detail_block = combined_text.split("Informacja o pojedynczych detalach/zleceniu", 1)[1].strip()
            if "Zlecenia wykonania" in detail_block:
                detail_block = detail_block.split("Zlecenia wykonania", 1)[0].strip()
        else:
            detail_block = ""

        print("Detail block (wycięty):")
        print(detail_block)

        detail_sections = re.split(r"(?im)^(?:#\s*)?Nr\s*(?:czesci|części):", detail_block)
        detail_sections = [sec.strip() for sec in detail_sections if sec.strip()]
        print("Found", len(detail_sections), "detail sections")

        details = []
        for sec in detail_sections:
            if "Plik geo:" in sec:
                det = parse_detail_section(sec)
                details.append(det)

        # Przypisujemy obrazy do detali, jeśli są dostępne
        images = extract_all_detail_images(doc)
        for i, det in enumerate(details):
            if i < len(images):
                det.image_path = copy_image_to_static(images[i])

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
