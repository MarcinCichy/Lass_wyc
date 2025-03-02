# pdf_utils.py
import fitz
import re
import os
import tempfile

def find_field(text: str, label: str) -> str:
    pattern = re.compile(rf"{label}:?\s*(.+)", re.IGNORECASE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""

def find_in_section(section: str, label: str) -> str:
    pattern = re.compile(rf"{label}:?\s*(.+)", re.IGNORECASE)
    match = pattern.search(section)
    return match.group(1).strip() if match else ""

def extract_all_detail_images(doc) -> list:
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
                images_with_page.extend(page_images)
    if images_with_page and images_with_page[0][0] == first_marker_page:
        images_with_page.pop(0)
    return [img_path for (pg, img_path) in images_with_page]

def extract_page_images(doc, page_number: int) -> list:
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

def extract_detail_name(full_path: str) -> str:
    lower_path = full_path.lower()
    geo_index = lower_path.rfind(".geo")
    if geo_index == -1:
        return full_path.strip()
    without_ext = full_path[:geo_index]
    slash_index = max(without_ext.rfind("\\"), without_ext.rfind("/"))
    if slash_index != -1:
        detail_name = without_ext[slash_index+1:]
    else:
        detail_name = without_ext
    return detail_name.strip()

def find_multiline_field(section: str, label: str) -> str:
    pattern = re.compile(rf"{label}:([\s\S]+?)(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]{{2,}}:|\Z)", re.IGNORECASE)
    match = pattern.search(section)
    if match:
        return " ".join(match.group(1).strip().split())
    return ""
