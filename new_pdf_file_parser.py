import re
from models import Program, Detail
from pdf_utils import find_field, find_in_section, extract_all_detail_images
from utils import copy_image_to_static

def parse_detail_section(section_text: str) -> Detail:
    """
    Parsuje blok tekstu z informacjami o detalu.
    Wyodrębnia nazwę, wymiary, ilość, czas obróbki oraz masę detalu.
    Czas obróbki (w formacie HH:MM:SS) jest przeliczany na godziny,
    a masa detalu (z etykiety "Masa detalu:") jest interpretowana jako kg.
    Wymiary są zaokrąglane do dwóch miejsc po przecinku.
    """
    text = section_text.strip()

    # Nazwa detalu
    det_name = ""
    match = re.search(r'Plik\s+geo:\s*(.+?\.geo)', text, re.IGNORECASE)
    if match:
        full_name = match.group(1).strip()
        if full_name.lower().endswith(".geo"):
            det_name = full_name[:-4].strip()
        else:
            det_name = full_name
    if not det_name:
        geo_matches = re.findall(r'([^\n]+?\.geo)', text, re.IGNORECASE)
        if geo_matches:
            full_name = geo_matches[-1].strip()
            if full_name.lower().endswith(".geo"):
                det_name = full_name[:-4].strip()
            else:
                det_name = full_name

    # Wymiary
    dims_match = re.search(r'(\d+,\d+\s*x\s*\d+,\d+\s*mm)', text, re.IGNORECASE)
    if dims_match:
        raw_dims = dims_match.group(1).strip()
        m = re.match(r"([\d,\.]+)\s*x\s*([\d,\.]+)", raw_dims)
        if m:
            x = float(m.group(1).replace(',', '.'))
            y = float(m.group(2).replace(',', '.'))
            dimensions = f"{x:.2f} x {y:.2f} mm"
        else:
            dimensions = raw_dims
    else:
        dimensions = ""

    # Ilość
    qty_match = re.search(r'Szt\.:\s*(\d+)', text, re.IGNORECASE)
    if not qty_match:
        qty_match = re.search(r'^\s*(\d+)\s*$', text, re.MULTILINE)
    try:
        quantity = int(qty_match.group(1).strip()) if qty_match else 1
    except Exception:
        quantity = 1

    # Czas obróbki – szukamy formatu HH:MM:SS
    time_match = re.search(r'(\d{2}:\d{2}:\d{2})', text)
    cut_time = 0
    if time_match:
        time_str = time_match.group(1)
        try:
            h, m, s = time_str.split(":")
            # Obliczamy całkowite sekundy, zaokrąglamy do najbliższej sekundy i konwertujemy na godziny
            total_seconds = int(round(int(h) * 3600 + int(m) * 60 + float(s)))
            cut_time = total_seconds / 3600.0
        except Exception:
            cut_time = 0
    elif text.strip().endswith("min"):
        try:
            minutes = float(text.replace("min", "").strip())
            total_seconds = int(round(minutes * 60))
            cut_time = total_seconds / 3600.0
        except Exception:
            cut_time = 0

    # Masa detalu – szukamy wartości zakończonej "kg" w etykiecie "Masa detalu:"
    weight_match = re.search(r'Masa detalu:\s*([\d,\.]+)\s*kg', text, re.IGNORECASE)
    if not weight_match:
        # Jeśli nie znalazło, spróbuj ogólnego wzorca
        weight_match = re.search(r'([\d,\.]+)\s*kg', text, re.IGNORECASE)
    if weight_match:
         try:
             weight = float(weight_match.group(1).replace(',', '.'))
         except Exception:
             weight = 0.0
    else:
         weight = 0.0

    return Detail(
        name=det_name,
        quantity=quantity,
        dimensions=dimensions,
        cut_time=cut_time,
        cut_length=0.0,
        weight=weight,
        image_path=None
    )

def parse_pdf_new(doc, full_text: str) -> Program:
    try:
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

        prog_name_match = re.search(r"Liczba detali:\s*Liczba arkuszy:\s*\n\s*(\S+)", combined_text,
                                    re.IGNORECASE | re.MULTILINE)
        program_name = prog_name_match.group(1).strip() if prog_name_match else ""

        rep_match = re.search(r"Czas\s+trwania\s*\n\s*(\S+)\s+(\d+)", combined_text,
                              re.IGNORECASE | re.MULTILINE)
        program_counts = int(rep_match.group(2)) if rep_match else 0

        material_match = re.search(r"[A-Z0-9]+----[0-9x]+\s*\((\d+\.\d+)\)", combined_text,
                                   re.IGNORECASE)
        material = material_match.group(1).strip() if material_match else ""

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
