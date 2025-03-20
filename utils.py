import os
import re
import shutil
import uuid

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

def copy_image_to_static(image_path: str) -> str:
    """
    Kopiuje plik obrazu z podanej ścieżki do katalogu static/images.
    Zwraca URL względny, np. "static/images/nazwa_pliku_unikalna.BMP".
    """
    dest_dir = os.path.join(os.getcwd(), 'static', 'images')
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    base_name = os.path.basename(image_path)
    name, ext = os.path.splitext(base_name)
    # Generujemy unikalny identyfikator i dodajemy go do nazwy pliku
    unique_name = f"{name}_{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(dest_dir, unique_name)
    try:
        shutil.copy(image_path, dest_path)
        print(f"Skopiowano obrazek z '{image_path}' do '{dest_path}'")
    except Exception as e:
        print("Błąd kopiowania obrazu:", e)
    return "static/images/" + unique_name
