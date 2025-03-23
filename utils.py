import os
import re
import shutil
import uuid
import atexit

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
    Kopiuje plik obrazu z podanej ścieżki do katalogu TEMP_IMAGE_DIR ("static/images/generated").
    Generuje unikalną nazwę, aby uniknąć konfliktów.
    Zwraca URL względny, np. "static/images/generated/nazwa_pliku_unikalna.BMP".
    """
    dest_dir = TEMP_IMAGE_DIR
    base_name = os.path.basename(image_path)
    name, ext = os.path.splitext(base_name)
    unique_name = f"{name}_{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(dest_dir, unique_name)
    try:
        shutil.copy(image_path, dest_path)
        print(f"Skopiowano obrazek z '{image_path}' do '{dest_path}'")
    except Exception as e:
        print("Błąd kopiowania obrazu:", e)
    return "static/images/generated/" + unique_name

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
