import re
import os

class Detail:
    def __init__(self, name: str):
        self.name = name
        self.points = []  # Lista punktów: [(x, y), ...]

    def add_point(self, x: float, y: float):
        self.points.append((x, y))

    def to_svg_string(self) -> str:
        if not self.points:
            return ""
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max_x - min_x or 1
        height = max_y - min_y or 1
        # Przesuń punkty tak, aby minimalna współrzędna była 0
        shifted = [(x - min_x, y - min_y) for (x, y) in self.points]
        points_str = " ".join(f"{x},{y}" for x, y in shifted)
        svg_content = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f'  <polygon points="{points_str}" fill="none" stroke="black" stroke-width="1"/>\n'
            f'</svg>\n'
        )
        return svg_content

    def save_to_svg(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.to_svg_string())

class LSTParser:
    def __init__(self):
        self.details = []  # Lista obiektów Detail

    def _parse_numbers(self, text: str) -> list:
        # Wyodrębnia liczby, np. z tekstu "X-0.605Y-1.751"
        numbers = re.findall(r'[-+]?\d*\.\d+|[-+]?\d+', text)
        return [float(n) for n in numbers]

    def parse_content(self, content: str) -> list:
        """
        Parsuje zawartość pliku LST i dzieli ją na sekcje START_TEXT/STOP_TEXT.
        Każda taka sekcja traktowana jest jako osobny detal.
        Wewnątrz sekcji wyodrębniamy linie, które zawierają współrzędne X i Y.
        """
        self.details = []
        # Znajdź wszystkie fragmenty między START_TEXT a STOP_TEXT
        sections = re.findall(r'START_TEXT(.*?)STOP_TEXT', content, flags=re.DOTALL)
        if not sections:
            print("Nie znaleziono sekcji START_TEXT/STOP_TEXT")
            return self.details

        for idx, sec in enumerate(sections, start=1):
            # Spróbuj wyodrębnić nazwę detalu z komentarza (np. "(NUMER DETALU:...)" )
            name_match = re.search(r'\(NUMER DETALU:(.*?)\)', sec)
            name = name_match.group(1).strip() if name_match else f"Detail_{idx}"
            detail = Detail(name)
            for line in sec.splitlines():
                line = line.strip()
                # Jeśli linia zawiera oba znaki X i Y, spróbuj wyodrębnić współrzędne.
                if 'X' in line and 'Y' in line:
                    # Opcjonalnie pomiń linie zawierające "TC_" – mogą to być komendy techniczne.
                    if "TC_" in line:
                        continue
                    nums = self._parse_numbers(line)
                    # Zakładamy, że pierwsze dwie liczby odpowiadają współrzędnym X i Y.
                    if len(nums) >= 2:
                        x, y = nums[0], nums[1]
                        detail.add_point(x, y)
            self.details.append(detail)
        return self.details

    def parse_file(self, file_path: str) -> list:
        with open(file_path, 'r', encoding='cp1250') as f:
            content = f.read()
        return self.parse_content(content)

    def save_details(self, output_dir: str):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for idx, det in enumerate(self.details, start=1):
            safe_name = re.sub(r'[^A-Za-z0-9_\-]', '_', det.name)
            if not safe_name:
                safe_name = f"detail_{idx}"
            filename = os.path.join(output_dir, f"detail_{idx}_{safe_name}.svg")
            det.save_to_svg(filename)
            print(f"Zapisano detal '{det.name}' do pliku: {filename}")

if __name__ == "__main__":
    # Przykład użycia:
    lst_file = "mc0929n5.LST"  # Podaj tutaj ścieżkę do Twojego pliku LST
    output_directory = "wyniki_svg"  # Folder, gdzie zapiszemy pliki SVG

    parser = LSTParser()
    details = parser.parse_file(lst_file)
    print(f"Znaleziono {len(details)} detali")
    for idx, d in enumerate(details, start=1):
        print(f"Detal {idx}: {d.name}, liczba punktów: {len(d.points)}")
    parser.save_details(output_directory)
