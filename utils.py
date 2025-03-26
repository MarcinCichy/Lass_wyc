import os
import re
import shutil
import uuid
import atexit
from PIL import Image

def normalize_filename(name: str) -> str:
    """
    Normalizuje nazwę pliku – zamienia sekwencje białych znaków na pojedynczą spację
    i usuwa białe znaki z początku i końca.
    """
    return re.sub(r'\s+', ' ', name).strip()

def find_file_recursive(directory: str, target_name: str) -> str:
    """
    Przeszukuje katalog 'directory' (rekursywnie) w poszukiwaniu pliku,
    którego znormalizowana nazwa (porównanie case-insensitive)
    odpowiada 'target_name' (również znormalizowanej).
    Zwraca pełną ścieżkę do pliku, jeśli zostanie znaleziony, lub None.
    """
    target_norm = normalize_filename(target_name).lower()
    for root, dirs, files in os.walk(directory):
        for f in files:
            if normalize_filename(f).lower() == target_norm:
                return os.path.join(root, f)
    return None

# Ustawiamy TEMP_IMAGE_DIR jako podfolder "generated" w katalogu static/images
TEMP_IMAGE_DIR = os.path.join(os.getcwd(), "static", "images", "generated")
if not os.path.exists(TEMP_IMAGE_DIR):
    os.makedirs(TEMP_IMAGE_DIR)


def copy_image_to_static(image_path: str) -> str:
    """
    Kopiuje lub konwertuje plik obrazu z podanej ścieżki do TEMP_IMAGE_DIR (static/images/generated).
    Jeśli obraz jest w formacie BMP, konwertuje go do PNG.
    Zwraca URL względny, np. "static/images/generated/nazwa_pliku_unikalna.png".
    """
    # Używamy TEMP_IMAGE_DIR jako docelowego katalogu
    dest_dir = TEMP_IMAGE_DIR
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    base_name = os.path.basename(image_path)
    name, ext = os.path.splitext(base_name)

    # Jeśli obraz jest BMP, konwertuj do PNG
    if ext.lower() == ".bmp":
        try:
            img = Image.open(image_path)
            unique_name = f"{name}_{uuid.uuid4().hex}.png"
            dest_path = os.path.join(dest_dir, unique_name)
            img.save(dest_path, format="PNG")
            print(f"Przekonwertowano BMP do PNG: {dest_path}")
        except Exception as e:
            print("Błąd konwersji BMP:", e)
            unique_name = f"{name}_{uuid.uuid4().hex}{ext}"
            dest_path = os.path.join(dest_dir, unique_name)
            shutil.copy(image_path, dest_path)
    else:
        unique_name = f"{name}_{uuid.uuid4().hex}{ext}"
        dest_path = os.path.join(dest_dir, unique_name)
        shutil.copy(image_path, dest_path)

    # Zwracamy ścieżkę względną, uwzględniając folder "generated"
    return os.path.join("static", "images", "generated", unique_name)

def clear_generated_images():
    """
    Usuwa wszystkie pliki w katalogu TEMP_IMAGE_DIR ("static/images/generated"),
    pozostawiając sam folder oraz inne pliki w static/images nietknięte.
    """
    for filename in os.listdir(TEMP_IMAGE_DIR):
        file_path = os.path.join(TEMP_IMAGE_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Usunięto: {file_path}")
        except Exception as e:
            print(f"Błąd przy usuwaniu {file_path}: {e}")

atexit.register(clear_generated_images)
