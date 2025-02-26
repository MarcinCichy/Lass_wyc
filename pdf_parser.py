import fitz  # PyMuPDF
import re
from models import Program, Detail

def parse_pdf(file_path: str) -> Program:
    """Parsuje plik PDF z danymi programu laserowego i zwraca obiekt Program."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    def find_field(label):
        pattern = re.compile(rf"{label}:\s*(.+)")
        match = pattern.search(text)
        return match.group(1).strip() if match else ""

    program_name = find_field("NAZWA PROGRAMU")
    material = find_field(r"MATERIAŁ \(ARKUSZ\)")
    machine_time = find_field("CZAS MASZYNOWY")
    try:
        program_counts = int(find_field("ILOŚĆ PRZEBIEGÓW PROGRAMU"))
    except ValueError:
        program_counts = 0
    thicknes = 0.0  # Jeśli nie ma informacji o grubości, ustawiamy domyślnie 0.0

    # Parsowanie detali – dzielimy tekst na segmenty po "INFORMACJA O DETALU"
    details = []
    detail_sections = re.split(r"INFORMACJA O DETALU", text)
    for section in detail_sections[1:]:
        geo_file = find_in_section(section, "NAZWA PLIKU GEO")
        try:
            quantity = int(find_in_section(section, "ILOŚĆ"))
        except ValueError:
            quantity = 1
        dimensions = find_in_section(section, "WYMIARY")
        try:
            cut_time = float(find_in_section(section, "CZAS OBRÓBKI").split()[0])
        except (ValueError, IndexError):
            cut_time = 0.0
        cut_length = 0.0
        weight = 0.0
        detail = Detail(
            name=geo_file,
            quantity=quantity,
            dimensions=dimensions,
            cut_time=cut_time,
            cut_length=cut_length,
            weight=weight,
            image_path=None  # PDF nie dostarcza informacji o obrazku
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
    return program

def find_in_section(section: str, label: str) -> str:
    """Pomocnicza funkcja wyszukująca wartość dla danego labela w sekcji tekstu."""
    pattern = re.compile(rf"{label}:\s*(.+)")
    match = pattern.search(section)
    return match.group(1).strip() if match else ""
