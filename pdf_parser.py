# pdf_parser.py
import fitz  # PyMuPDF
import re
import os
import tempfile
from models import Program, Detail

def parse_pdf(file_path: str) -> Program:
    """
    Parsuje plik PDF (stary lub nowy format) i zwraca obiekt Program.
    Wyodrębnia dane programu oraz detali takie same jak w HTML.
    Dla detali pobiera obraz (rysunek) z sekcji – zapisuje go tymczasowo.
    """
    doc = fitz.open(file_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text")

    # Wyodrębnianie danych programu (analogicznie do HTML)
    program_name_full = find_field(full_text, "NAZWA PROGRAMU")
    program_name = program_name_full[:-2] if len(program_name_full) >= 2 else program_name_full
    material = find_field(full_text, r"MATERIAŁ \(ARKUSZ\)")
    machine_time_full = find_field(full_text, "CZAS MASZYNOWY")
    machine_time = machine_time_full[0:11] if len(machine_time_full) >= 11 else machine_time_full
    try:
        program_counts = int(find_field(full_text, "ILOŚĆ PRZEBIEGÓW PROGRAMU"))
    except ValueError:
        program_counts = 0
    # Grubość – analogicznie do HTML, zakładamy format np. "St37-30 (1.0038)"
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

    ###### DETAILS SECTION

    # W zależności od formatu PDF wybieramy fragment tekstu z danymi detali:
    if "Informacja o pojedynczych detalach/zleceniu" in full_text:
        details_text = full_text.split("Informacja o pojedynczych detalach/zleceniu", 1)[1]
    elif full_text.count("INFORMACJA O DETALU") >= 2:
        parts = full_text.split("INFORMACJA O DETALU")
        details_text = parts[2]  # po drugim wystąpieniu
    else:
        details_text = ""

    # Rozdzielamy sekcje detali – zakładamy, że każda sekcja zaczyna się od markeru "NUMER CZĘŚCI:"
    detail_sections = re.split(r"NUMER CZĘŚCI:", details_text)
    detail_sections = detail_sections[1:]  # pomijamy pierwszy element

    # Pobierz obrazy ze stron PDF zaczynając od pierwszej strony z markerem
    images = extract_all_detail_images(doc)
    # Jeśli liczba obrazów jest równa liczbie detali + 1, usuwamy ostatni (rysunek arkusza)
    if len(images) == len(detail_sections) + 1:
        images.pop()
    # Dodatkowo – jeżeli pierwszy obraz pochodzi z tej samej strony, na której występuje pierwszy marker,
    # zakładamy, że to logo i usuwamy je.
    # (W naszej funkcji extract_all_detail_images będziemy zwracać informacje o stronie, więc możemy to sprawdzić)
    # W tym przykładzie zmodyfikujemy funkcję tak, aby zwracała tylko ścieżki obrazów po odpowiedniej filtracji.

    print(f"Obrazów: {len(images)}, Detali: {len(detail_sections)}")
    details = []
    image_index = 0

    for sec in detail_sections:
        # Dla każdej sekcji wyodrębniamy pola: NAZWA PLIKU GEO, ILOŚĆ, WYMIARY, CZAS OBRÓBKI.
        # Wyciągamy nazwę detalu – usuwamy ścieżkę i rozszerzenie
        geo_name_full = find_in_section(sec, "NAZWA PLIKU GEO:")
        geo_name = os.path.basename(geo_name_full)
        geo_name, _ = os.path.splitext(geo_name)

        quantity = find_in_section(sec, "ILOŚĆ")
        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1

        dimensions = find_in_section(sec, "WYMIARY")
        cut_time_str = find_in_section(sec, "CZAS OBRÓBKI")
        try:
            cut_time = float(cut_time_str.split()[0])
        except (ValueError, IndexError):
            cut_time = 0.0

        cut_length = 0.0
        weight = 0.0

        if image_index < len(images):
            image_path = images[image_index]
            image_index += 1
        else:
            image_path = None

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
        print(f"Detail: {detail}")

    doc.close()

    program = Program(
        name=program_name,
        material=prog_material,
        thicknes=thicknes,
        machine_time=machine_time,
        program_counts=program_counts,
        details=details
    )
    print(f"Program: {program}")
    return program

def find_field(text: str, label: str) -> str:
    """
    Wyszukuje wartość dla danego labela w tekście.
    """
    pattern = re.compile(rf"{label}:?\s*(.+)", re.IGNORECASE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""

def find_in_section(section: str, label: str) -> str:
    """
    Wyszukuje wartość dla danego labela w sekcji tekstu.
    """
    pattern = re.compile(rf"{label}:?\s*(.+)", re.IGNORECASE)
    match = pattern.search(section)
    return match.group(1).strip() if match else ""

def extract_all_detail_images(doc) -> list:
    """
    Wyodrębnia obrazy ze stron dokumentu PDF, zaczynając od strony z pierwszym markerem detalu
    aż do końca dokumentu. Zwraca listę ścieżek do obrazów (po usunięciu obrazu logo, jeśli wystąpi).
    """
    first_marker_page = None
    for page in doc:
        page_text = page.get_text("text")
        if ("INFORMACJA O DETALU" in page_text) or ("Informacja o pojedynczych detalach/zleceniu" in page_text):
            first_marker_page = page.number
            break

    images_with_page = []
    if first_marker_page is not None:
        for page in doc:
            if page.number >= first_marker_page:
                page_images = extract_page_images(doc, page.number)
                # page_images zawiera listę krotek: (page_number, image_path)
                images_with_page.extend(page_images)
    # Usuń pierwszy obraz, jeśli pochodzi z first_marker_page (zakładamy, że to logo)
    if images_with_page and images_with_page[0][0] == first_marker_page:
        images_with_page.pop(0)
    # Jeśli liczba obrazów wynosi liczba detali + 1, usuń ostatni obraz (rysunek całego arkusza)
    # (Ta logika zostanie wykonana w parserze głównym)
    return [img_path for (pg, img_path) in images_with_page]

def extract_page_images(doc, page_number: int) -> list:
    """
    Wyodrębnia obrazy z danej strony PDF i zapisuje je do tymczasowych plików BMP.
    Zwraca listę krotek: (page_number, image_path)
    """
    page = doc.load_page(page_number)
    image_info = page.get_images(full=True)
    image_tuples = []
    for img in image_info:
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        temp_dir = tempfile.gettempdir()
        image_filename = f"pdf_img_page{page_number}_xref{xref}.bmp"
        image_path = os.path.join(temp_dir, image_filename)
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        image_tuples.append((page_number, image_path))
    return image_tuples
