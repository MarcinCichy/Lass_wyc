import os
import ntpath
import re
from bs4 import BeautifulSoup, Comment
from models import Program, Detail
from utils import copy_image_to_static, normalize_filename, find_file_recursive

def parse_html(file_path: str) -> Program:
    """Parsuje plik HTML z danymi programu laserowego i zwraca obiekt Program."""
    with open(file_path, "r", encoding="cp1250") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')

    # Odczytujemy wszystkie komentarze
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    # Parsowanie danych programu z komentarzy
    program_name = ""
    material = ""
    thicknes = ""
    machine_time = ""
    program_counts = ""

    for comment in comments:
        if comment.strip() == "Programm-Nummer und Bemerkung":
            tr = comment.find_next_sibling('tr')
            if tr:
                b_tag = tr.find('b')
                if b_tag:
                    program_name = b_tag.get_text(strip=True)
        elif comment.strip() == "Material (Technologietabelle)":
            tr = comment.find_next_sibling('tr')
            if tr:
                b_tag = tr.find('b')
                if b_tag:
                    material_string = b_tag.get_text(strip=True)
                    material_sub = material_string[:10]
                    try:
                        minus_index = material_sub.index('-')
                        material = material_sub[:minus_index]
                    except ValueError:
                        material = material_sub
                    try:
                        thicknes_str = material_string[minus_index + 1:minus_index + 2].strip()
                        thicknes = abs(float(thicknes_str))
                    except (ValueError, UnboundLocalError):
                        thicknes = 10000
        elif comment.strip() == "Maschinenzeit/Tafel":
            tr = comment.find_next_sibling('tr')
            if tr:
                nobr_tag = tr.find('nobr')
                if nobr_tag:
                    text = nobr_tag.get_text(strip=True)
                    index = text.find('[')
                    machine_time = text[:index].strip() if index != -1 else text
        elif comment.strip() == "Anzahl Programmdurchlauefe":
            tr = comment.find_next('tr')
            if tr:
                tds = tr.find_all('td')
                for td in tds:
                    txt = td.get_text(strip=True)
                    if txt.isdigit():
                        program_counts = int(txt)
                        break

    # Parsowanie detali z sekcji "HTML-Block: Einzelteil-Informationen mit Grafiken, ohne Barcode"
    details = []
    detail_comment = None
    for comment in comments:
        if comment.strip() == "HTML-Block: Einzelteil-Informationen mit Grafiken, ohne Barcode":
            detail_comment = comment
            break
    if detail_comment:
        table = detail_comment.find_next('table')
        if table:
            rows = table.find_all('tr')
            i = 0
            while i < len(rows):
                tds = rows[i].find_all('td')
                # Sprawdzamy, czy w drugiej komórce jest napis "NUMER CZĘŚCI:" – to początek bloku detalu
                if len(tds) >= 2 and "NUMER CZĘŚCI:" in tds[1].get_text(strip=True):
                    detail_data = {}
                    # Pobieramy obrazek z pierwszej komórki
                    img_tag = tds[0].find("img")
                    if img_tag and img_tag.has_attr("src"):
                        image_src = img_tag["src"].strip()
                        # Normalizujemy nazwę (usuwa nadmiarowe białe znaki)
                        image_src_norm = normalize_filename(image_src)
                        base = os.path.basename(image_src_norm)
                        directory = os.path.dirname(file_path)
                        # Przeszukujemy katalog (rekursywnie), aby znaleźć plik (porównanie case-insensitive)
                        original_image_path = find_file_recursive(directory, base)
                        print(f"Normalized image path: {repr(original_image_path)}")
                        if original_image_path and os.path.exists(original_image_path):
                            image_path = copy_image_to_static(original_image_path)
                            print(f"Image copied to: {image_path}")
                        else:
                            image_path = None
                            print("File not found after normalization.")
                    else:
                        image_path = None
                    # Parsujemy pozostałe dane detalu (przyjmujemy blok około 15 wierszy)
                    for j in range(i, min(i + 15, len(rows))):
                        cells = rows[j].find_all('td')
                        if len(cells) < 2:
                            continue
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key == "NAZWA PLIKU GEO:":
                            value = ntpath.basename(value)
                            value_pure = ntpath.splitext(value)[0]
                            detail_data["geo_file"] = value_pure
                        elif key == "ILOŚĆ:":
                            try:
                                detail_data["quantity"] = int(value)
                            except ValueError:
                                detail_data["quantity"] = 1
                        elif key == "WYMIARY:":
                            detail_data["dimensions"] = value
                        elif key == "CZAS OBRÓBKI:":
                            try:
                                detail_data["cut_time"] = float(value[:5])
                            except ValueError:
                                detail_data["cut_time"] = 0.0
                    if ("geo_file" in detail_data and "quantity" in detail_data and
                        "dimensions" in detail_data and "cut_time" in detail_data):
                        detail_data.setdefault("cut_length", 0.0)
                        detail_data.setdefault("weight", 0.0)
                        detail = Detail(
                            name=detail_data["geo_file"],
                            quantity=detail_data["quantity"],
                            dimensions=detail_data["dimensions"],
                            cut_time=detail_data["cut_time"],
                            cut_length=detail_data["cut_length"],
                            weight=detail_data["weight"],
                            image_path=image_path if image_path and os.path.exists(image_path) else None
                        )
                        details.append(detail)
                    i += 15  # pomijamy cały blok detalu
                else:
                    i += 1

    program = Program(
        name=program_name,
        material=material,
        thicknes=thicknes,
        machine_time=machine_time,
        program_counts=program_counts,
        details=details
    )
    return program
