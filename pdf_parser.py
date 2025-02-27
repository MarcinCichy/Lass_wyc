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
    program_name = find_field(full_text, "NAZWA PROGRAMU")
    material = find_field(full_text, r"MATERIAŁ \(ARKUSZ\)")
    machine_time = find_field(full_text, "CZAS MASZYNOWY")
    try:
        program_counts = int(find_field(full_text, "ILOŚĆ PRZEBIEGÓW PROGRAMU"))
    except ValueError:
        program_counts = 0
    # Grubość wyciągamy analogicznie – przyjmujemy, że materiał ma format np. "St37-30 (1.0038)"
    # Użyjemy podobnej logiki jak w html_parser.py:
    material_sub = material[:10]
    try:
        minus_index = material_sub.index('-')
        prog_material = material_sub[:minus_index]
    except ValueError:
        prog_material = material_sub
    try:
        thicknes_str = material[minus_index + 1:minus_index + 5].strip()
        thicknes = abs(float(thicknes_str))
    except (ValueError, UnboundLocalError):
        thicknes = 0.0

    # Wyodrębniamy tekst sekcji detali w zależności od formatu
    if "Informacja o pojedynczych detalach/zleceniu" in full_text:
        details_text = full_text.split("Informacja o pojedynczych detalach/zleceniu", 1)[1]
    elif full_text.count("INFORMACJA O DETALU") >= 2:
        parts = full_text.split("INFORMACJA O DETALU")
        details_text = parts[2]  # po drugim wystąpieniu
    else:
        details_text = ""

    # Rozdzielamy sekcje detali – zakładamy, że każdy detal zaczyna się od pojawienia się pola "NAZWA PLIKU GEO:"
    detail_sections = re.split(r"NAZWA PLIKU GEO:", details_text)
    # Pierwszy element może zawierać dane nie należące do detali, więc pomijamy go
    detail_sections = detail_sections[1:]

    details = []
    # Pobierz obrazy ze stron PDF, które zawierają sekcje detali.
    # Przyjmujemy, że obrazy są uporządkowane – wyodrębniamy wszystkie obrazy z całego dokumentu
    images = extract_all_detail_images(doc)
    image_index = 0  # indeks obrazu do przypisania

    for sec in detail_sections:
        # Dla każdej sekcji próbujemy wyodrębnić pola:
        # Ilość, WYMIARY, CZAS OBRÓBKI
        # Używamy pomocniczej funkcji find_in_section
        geo_field = sec.splitlines()[
            0].strip()  # bo podział nastąpił po "NAZWA PLIKU GEO:"; pierwsza linia zawiera resztę tekstu
        # Z geo_field wyciągamy tylko nazwę – usuwamy ścieżkę i rozszerzenie
        geo_name = os.path.basename(geo_field)
        geo_name, _ = os.path.splitext(geo_name)

        quantity = find_in_section(sec, "ILOŚĆ")
        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1

        dimensions = find_in_section(sec, "WYMIARY")
        # Załóżmy, że wymiary są w formacie "60.000 x 78.000 mm"
        # Możemy je zachować jako jeden ciąg – dalsze przetwarzanie może być w GUI
        cut_time_str = find_in_section(sec, "CZAS OBRÓBKI")
        try:
            # Weź tylko pierwszą wartość (np. "0.12" z "0.12 min (PierceLine: 0.12 min)")
            cut_time = float(cut_time_str.split()[0])
        except (ValueError, IndexError):
            cut_time = 0.0

        # Dla uproszczenia nie przetwarzamy cut_length ani weight – ustawiamy 0.0
        cut_length = 0.0
        weight = 0.0

        # Pobieramy obraz dla tego detalu – o ile mamy jeszcze obrazy
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

    doc.close()

    program = Program(
        name=program_name,
        material=prog_material,
        thicknes=thicknes,
        machine_time=machine_time,
        program_counts=program_counts,
        details=details
    )
    return program


def find_field(text: str, label: str) -> str:
    """
    Wyszukuje wartość dla danego labela w tekście.
    """
    pattern = re.compile(rf"{label}:\s*(.+)")
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def find_in_section(section: str, label: str) -> str:
    """
    Wyszukuje wartość dla danego labela w sekcji tekstu.
    """
    pattern = re.compile(rf"{label}:\s*(.+)")
    match = pattern.search(section)
    return match.group(1).strip() if match else ""


def extract_all_detail_images(doc) -> list:
    """
    Wyodrębnia obrazy z całego dokumentu PDF, które znajdują się w sekcjach detali.
    Zakładamy, że obrazy te pojawiają się w kolejności odpowiadającej kolejności detali.
    Obrazy zapisywane są do tymczasowych plików BMP.
    """
    images = []
    for page in doc:
        page_text = page.get_text("text")
        # Sprawdzamy, czy strona zawiera marker detalu
        if ("INFORMACJA O DETALU" in page_text) or ("Informacja o pojedynczych detalach/zleceniu" in page_text):
            page_images = extract_page_images(doc, page.number)
            images.extend(page_images)
    return images


def extract_page_images(doc, page_number: int) -> list:
    """
    Wyodrębnia obrazy z danej strony PDF i zapisuje je do tymczasowych plików BMP.
    Zwraca listę ścieżek do zapisanych obrazów.
    """
    page = doc.load_page(page_number)
    image_info = page.get_images(full=True)
    image_paths = []
    for img in image_info:
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        temp_dir = tempfile.gettempdir()
        image_filename = f"pdf_img_page{page_number}_xref{xref}.bmp"
        image_path = os.path.join(temp_dir, image_filename)
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        image_paths.append(image_path)
    return image_paths
