import os
import shutil
import uuid

def copy_image_to_static(image_path: str) -> str:
    """
    Kopiuje plik obrazu z podanej ścieżki do katalogu static/images.
    Zwraca URL względny, np. "static/images/nazwa_pliku_unikalny.bmp".
    """
    dest_dir = os.path.join(os.getcwd(), 'static', 'images')
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    base_name = os.path.basename(image_path)
    # Generujemy unikalny identyfikator i wstawiamy go przed rozszerzenie
    unique_id = uuid.uuid4().hex
    name, ext = os.path.splitext(base_name)
    new_name = f"{name}_{unique_id}{ext}"
    dest_path = os.path.join(dest_dir, new_name)
    try:
        shutil.copy(image_path, dest_path)
        print(f"Skopiowano obrazek z '{image_path}' do '{dest_path}'")
    except Exception as e:
        print("Błąd kopiowania obrazu:", e)
    return "static/images/" + new_name
