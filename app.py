from flask import Flask, render_template, request, jsonify
import os
import ntpath
from html_parser import parse_html
from pdf_parser import parse_pdf
from config import load_config, save_config

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Wczytanie konfiguracji przy starcie aplikacji
config = load_config()

def serialize_program(program):
    """Konwertuje obiekt program na słownik."""
    details = []
    for d in program.details:
        dims = d.dimensions.replace("mm", "").strip().split("x")
        dim_x = dims[0].strip() if len(dims) >= 1 else ""
        dim_y = dims[1].strip() if len(dims) >= 2 else ""
        detail_dict = {
            "image_path": d.image_path,
            "name": d.name,
            "dimensions": d.dimensions,
            "dim_x": dim_x,
            "dim_y": dim_y,
            "bending_count": 0,   # Domyślnie 0
            "cut_time": d.cut_time,
            "quantity": d.quantity,
            "weight": d.weight,   # Wartość potrzebna do obliczenia kosztu materiału
            "cutting_cost": d.cutting_cost(config, program.material),
            "material_cost": d.material_cost(config, program.material),
            "total_cost": d.total_cost(config, program.material),
            "total_cost_quantity": d.total_cost(config, program.material) * d.quantity
        }
        details.append(detail_dict)
    return {
        "name": program.name,
        "material": program.material,
        "thicknes": program.thicknes,
        "machine_time": program.machine_time,
        "program_counts": program.program_counts,
        "details": details,
        "total_cost": program.total_cost(config)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "Brak pliku"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nie wybrano pliku"}), 400
    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filename)
    ext = os.path.splitext(filename)[1].lower()
    program = None
    if ext == ".html":
        program = parse_html(filename)
    elif ext == ".pdf":
        program = parse_pdf(filename)
    else:
        return jsonify({"error": "Nieobsługiwany typ pliku"}), 400

    program_data = serialize_program(program)
    return jsonify(program_data)

@app.route('/update_config', methods=['POST'])
def update_config():
    data = request.json
    if not data:
        return jsonify({"error": "Brak danych"}), 400
    # Zapisujemy nową konfigurację do pliku
    save_config(data)
    # Aktualizujemy globalną konfigurację
    global config
    config = load_config()
    return jsonify({"success": True, "config": config})

@app.route('/get_config', methods=['GET'])
def get_config():
    # Zwraca aktualną konfigurację jako JSON
    return jsonify(config)

if __name__ == '__main__':
    app.run(debug=True)
