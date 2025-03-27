import re
from models import Program, Detail
from pdf_utils import find_field, find_in_section, extract_all_detail_images, extract_detail_name, find_multiline_field
from utils import copy_image_to_static

def parse_pdf_old(doc, full_text: str) -> Program:
    """
    Parsuje plik PDF starego typu – dodatkowo wyodrębnia:
      - czas obróbki z etykiety "CZAS OBRÓBKI:" (wartość w minutach) przeliczany na godziny,
        przy czym najpierw przeliczamy minuty na sekundy (zaokrąglając do najbliższej sekundy),
        a następnie dzielimy przez 3600.
      - wagę detalu z etykiety "CIĘŻAR:" (wartość zakończona "kg").
      Wymiary są zaokrąglane do dwóch miejsc po przecinku.
    """
    program_name_full = find_field(full_text, "NAZWA PROGRAMU")
    program_name = program_name_full[:-2] if len(program_name_full) >= 2 else program_name_full
    material = find_field(full_text, r"MATERIAŁ \(ARKUSZ\)")
    machine_time_full = find_field(full_text, "CZAS MASZYNOWY")
    machine_time = machine_time_full[0:11] if len(machine_time_full) >= 11 else machine_time_full
    try:
        program_counts = int(find_field(full_text, "ILOŚĆ PRZEBIEGÓW PROGRAMU"))
    except ValueError:
        program_counts = 0
    material_sub = material[:10]
    try:
        minus_index = material_sub.index('-')
        prog_material = material_sub[:minus_index]
    except ValueError:
        prog_material = material_sub
    try:
        thicknes_str = material[minus_index + 1:minus_index + 2].strip()
        thicknes = abs(float(thicknes_str))
    except (ValueError, UnboundLocalError):
        thicknes = 0.0

    print("Stary PDF:")
    print("1. NAZWA PROGRAMU:", program_name)
    print("2. MATERIAŁ (ARKUSZ):", material)
    print("3. CZAS MASZYNOWY:", machine_time)
    print("4. ILOŚĆ PRZEBIEGÓW PROGRAMU:", program_counts)
    print("5. PROG_MATERIAL:", prog_material)
    print("6. GRUBOŚĆ:", thicknes)

    if "Informacja o pojedynczych detalach/zleceniu" in full_text:
        details_text = full_text.split("Informacja o pojedynczych detalach/zleceniu", 1)[1]
    elif full_text.count("INFORMACJA O DETALU") >= 2:
        parts = full_text.split("INFORMACJA O DETALU")
        details_text = parts[2]
    else:
        details_text = ""

    detail_sections = re.split(r"NUMER CZĘŚCI:", details_text)[1:]
    images = extract_all_detail_images(doc)
    if len(images) == len(detail_sections) + 1:
        images.pop()
    details = []
    image_index = 0
    detail_counter = 1
    for sec in detail_sections:
        geo_name_full = find_multiline_field(sec, "NAZWA PLIKU GEO")
        geo_name = extract_detail_name(geo_name_full)
        quantity = find_in_section(sec, "ILOŚĆ")
        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1
        raw_dimensions = find_in_section(sec, "WYMIARY")
        m = re.match(r"([\d,\.]+)\s*x\s*([\d,\.]+)", raw_dimensions)
        if m:
            x = float(m.group(1).replace(',', '.'))
            y = float(m.group(2).replace(',', '.'))
            dimensions = f"{x:.2f} x {y:.2f} mm"
        else:
            dimensions = raw_dimensions
        cut_time_str = find_in_section(sec, "CZAS OBRÓBKI")
        # Usuwamy dodatkowe teksty, wyciągamy tylko liczbę przed "min"
        m = re.search(r'([\d\.]+)\s*min', cut_time_str, re.IGNORECASE)
        if m:
            minutes = float(m.group(1))
            total_seconds = int(round(minutes * 60))
            cut_time = total_seconds / 3600.0
        else:
            cut_time = 0.0
        weight_str = find_in_section(sec, "CIĘŻAR")
        if weight_str.endswith("kg"):
            m = re.search(r'([\d,\.]+)\s*kg', weight_str, re.IGNORECASE)
            if m:
                weight = float(m.group(1).replace(',', '.'))
            else:
                weight = 0.0
        else:
            weight = 0.0

        cut_length = 0.0

        if image_index < len(images):
            original_image_path = images[image_index]
            image_index += 1
            image_path = copy_image_to_static(original_image_path)
        else:
            image_path = None

        print(f"Detail {detail_counter} (stary PDF):")
        print("   NAZWA PLIKU GEO:", geo_name)
        print("   ILOŚĆ:", quantity)
        print("   WYMIARY:", dimensions)
        print("   CZAS OBRÓBKI (godz):", cut_time)
        print("   WAGA (kg):", weight)
        detail_counter += 1

        detail = Detail(
            name=geo_name,
            quantity=quantity,
            dimensions=dimensions,
            cut_time=cut_time,
            cut_length=cut_length,
            weight=weight,
            image_path=image_path
        )
        details.append(detail)

    program = Program(
        name=program_name,
        material=prog_material,
        thicknes=thicknes,
        machine_time=machine_time,
        program_counts=program_counts,
        details=details
    )
    print("Program (stary PDF):", program)
    return program
