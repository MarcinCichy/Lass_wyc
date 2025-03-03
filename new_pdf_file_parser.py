# new_pdf_file_parser.py
import re
from models import Program, Detail
from pdf_utils import find_field, find_in_section, extract_all_detail_images


def parse_pdf_new(doc, full_text: str) -> Program:
    # Tymczasowy kod do wypisania numeracji wszystkich linii dokumentu
    print("=== Numeracja linii dokumentu ===")
    for i, line in enumerate(full_text.splitlines(), start=1):
        print(f"{i}: {line}")
    print("=== Koniec numeracji linii dokumentu ===")

    # Pozostała część funkcji...
    # --- 1. Nazwa programu
    prog_name_match = re.search(r"Liczba detali:\s*Liczba arkuszy:\s*\n\s*(\S+)", full_text)
    if prog_name_match:
        program_name = prog_name_match.group(1).strip()
    else:
        program_name = ""

    # --- 2. Ilość powtórzeń programu
    rep_match = re.search(r"Czas\s+trwania\s*\n\s*(\S+)\s+(\d+)", full_text)
    if rep_match:
        program_counts = int(rep_match.group(2))
    else:
        program_counts = 0

    # --- 3. Materiał i grubość
    mat_block = re.search(
        r"Arkusz blachy do obróbki, pakiet\s*:?[\r\n]+(.+)[\r\n]+(.+)[\r\n]+Wymiary:",
        full_text
    )
    if mat_block:
        material = mat_block.group(1).strip()
        # Pobieramy wymiary – zakładamy, że po "Wymiary:" występuje linia z wymiarami
        dims_match = re.search(r"Wymiary:\s*\n\s*(.+)", full_text)
        if dims_match:
            dims_full = dims_match.group(1).strip()  # np. "3000,00 x 1500,00 x 3,00 mm"
            parts = dims_full.split("x")
            if len(parts) >= 3:
                thick_str = parts[2].strip().split()[0].replace(",", ".")
                thicknes = abs(float(thick_str))
            else:
                thicknes = 0.0
        else:
            thicknes = 0.0
    else:
        material = ""
        thicknes = 0.0

    # --- 4. Czas trwania maszyny
    machine_time = find_field(full_text, "Czas trwania")

    print("Nowy PDF:")
    print("1. Nazwa programu:", program_name)
    print("2. Materiał:", material)
    print("3. Czas trwania:", machine_time)
    print("4. Ilość powtórzeń programu:", program_counts)
    print("5. GRUBOŚĆ:", thicknes)

    # --- 5. Parsowanie sekcji detali
    if "Informacja o pojedynczych detalach/zleceniu" in full_text:
        detail_block = full_text.split("Informacja o pojedynczych detalach/zleceniu", 1)[1].strip()
    else:
        detail_block = ""

    # Dzielimy blok detali na segmenty przy użyciu pustych linii jako separatora
    detail_parts = re.split(r"\n\s*\n", detail_block)
    if len(detail_parts) < 4:
        print("Nie udało się poprawnie podzielić sekcji detali.")
        details = []  # Ustawiamy pustą listę, aby uniknąć błędu
    else:
        # Segment 1: wartości pierwszej grupy (m.in. Plik geo, Wymiary)
        values_part_1 = detail_parts[1].strip().splitlines()
        # Segment 2: wartości drugiej grupy (m.in. Szt., Czas obróbki detalu)
        values_part_2 = detail_parts[3].strip().splitlines()

        if len(values_part_1) >= 5:
            det_name = values_part_1[3].strip()
            dims_str = values_part_1[4].strip()
            dims_parts = dims_str.split("x")
            if len(dims_parts) >= 2:
                dim_x = dims_parts[0].strip()
                dim_y = dims_parts[1].strip().split()[0]
            else:
                dim_x = dims_str
                dim_y = ""
        else:
            det_name = ""
            dims_str = ""
            dim_x = ""
            dim_y = ""

        if len(values_part_2) >= 3:
            try:
                quantity = int(values_part_2[0].strip())
            except ValueError:
                quantity = 1
            cut_time = values_part_2[2].strip()  # zachowujemy jako string, np. "00:00:03"
        else:
            quantity = 1
            cut_time = "0"

        details = []
        images = extract_all_detail_images(doc)
        image_path = images[0] if images else None

        print("Detail 1 (nowy PDF):")
        print("   Plik geo (nazwa detalu):", det_name)
        print("   Wymiary: x =", dim_x, ", y =", dim_y)
        print("   Czas obróbki detalu:", cut_time)
        print("   Szt. (ilość):", quantity)
        print("   Materiał:", material)
        print("   GRUBOŚĆ:", thicknes)

        detail = Detail(
            name=det_name,
            quantity=quantity,
            dimensions=dims_str,  # ewentualnie: f"{dim_x} x {dim_y}"
            cut_time=cut_time,
            cut_length=0.0,
            weight=0.0,
            image_path=image_path
        )
        details.append(detail)

    program = Program(
        name=program_name,
        material=material,
        thicknes=thicknes,
        machine_time=machine_time,
        program_counts=program_counts,
        details=details
    )
    print("Program (nowy PDF):", program)
    return program

