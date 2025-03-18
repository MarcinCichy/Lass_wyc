import os
import shutil

def copy_image_to_static(image_path: str) -> str:
    """
    Kopiuje plik obrazu z podanej ścieżki do katalogu static/images.
    Zwraca URL względny, np. "static/images/nazwa_pliku.bmp".
    """
    dest_dir = os.path.join(os.getcwd(), 'static', 'images')
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    base_name = os.path.basename(image_path)
    dest_path = os.path.join(dest_dir, base_name)
    try:
        shutil.copy(image_path, dest_path)
    except Exception as e:
        print("Błąd kopiowania obrazu:", e)
    return "static/images/" + base_name
