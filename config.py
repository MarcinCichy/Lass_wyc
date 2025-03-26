import json
import os

CONFIG_FILE = "config.json"

default_config = {
    "cutting_costs": {
        "stal_czarna": 5.0,
        "stal_nierdzewna": 6.0,
        "aluminium": 4.5
    },
    "material_costs": {
        "stal_czarna": 2.5,
        "stal_nierdzewna": 3.0,
        "aluminium": 1.5
    },
    "suma_kosztow_giecia": 0.0
}

def load_config() -> dict:
    """Wczytuje ustawienia z pliku JSON; jeśli plik nie istnieje, tworzy go z wartościami domyślnymi."""
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config.copy()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Uzupełnij brakujące klucze wartościami domyślnymi
    for key, value in default_config.items():
        if key not in data:
            data[key] = value
    return data

def save_config(config_data: dict):
    """Zapisuje ustawienia do pliku JSON."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
