import re
import os
import math


def close_contour(points, tolerance=0.5):
    """
    Sprawdza, czy pierwszy i ostatni punkt listy są blisko siebie.
    Jeśli nie, dodaje pierwszy punkt na końcu, aby zamknąć kontur.

    :param points: Lista punktów [(x, y), ...]
    :param tolerance: Maksymalne dopuszczalne odchylenie (mm), by uznać, że kontur jest zamknięty.
    :return: Lista punktów (może być wydłużona o pierwszy punkt, jeśli był brak zamknięcia)
    """
    if not points:
        return points
    first = points[0]
    last = points[-1]
    if math.hypot(first[0] - last[0], first[1] - last[1]) > tolerance:
        points.append(first)
    return points


class Detail:
    """
    Klasa reprezentująca pojedynczy detal z pliku LST.
    Zawiera nazwę oraz listę punktów, które reprezentują geometrię (kontur).
    """

    def __init__(self, name: str):
        self.name = name if name else "Unnamed_Detail"
        self.points = []  # Lista punktów (x, y)

    def add_point(self, x: float, y: float):
        self.points.append((x, y))

    def to_svg_string(self, margin=10) -> str:
        """
        Generuje zawartość pliku SVG dla danego detalu.
        Przed generowaniem, kontur jest zamykany (jeśli różnica między pierwszym a ostatnim punktem jest mniejsza niż tolerancja).

        :param margin: Margines wokół rysunku.
        :return: Ciąg znaków zawierający kod SVG.
        """
        pts = close_contour(self.points.copy())
        if not pts:
            return ""
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = (max_x - min_x) + 2 * margin
        height = (max_y - min_y) + 2 * margin

        # Przesunięcie punktów, aby rysunek zaczynał się od (margin, margin)
        shifted_points = [(x - min_x + margin, y - min_y + margin) for x, y in pts]
        points_str = " ".join(f"{x},{y}" for x, y in shifted_points)
        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'  <polygon points="{points_str}" fill="none" stroke="black" stroke-width="1" />',
            '</svg>'
        ]
        return "\n".join(svg_lines)

    def save_to_svg(self, filename: str, margin=10):
        svg_content = self.to_svg_string(margin)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(svg_content)


class LSTParser:
    """
    Parser plików LST, który wyodrębnia informacje o programie i detale (geometrię).
    Obsługuje zarówno starsze, jak i nowsze formaty plików LST.
    """

    def __init__(self):
        self.details = []  # Lista obiektów typu Detail

    def _parse_numbers_from_line(self, line: str) -> list:
        """
        Wyodrębnia wszystkie liczby (float) z danej linii tekstu.

        :param line: Linia tekstu.
        :return: Lista liczb.
        """
        # Zamiana separatorów na spacje
        line = line.replace('\t', ' ').replace(';', ' ')
        # Usuwanie zbędnych znaków
        line = line.strip()
        tokens = []
        for token in line.split():
            # Obsługa wyrażeń typu "X=100" lub "Y:-200"
            token = re.sub(r'^[A-Za-z]+[=:]', '', token)
            token = token.strip(" ,;()")
            # Jeśli token zawiera przecinek jako separator dziesiętny, zamień na kropkę
            token = token.replace(',', '.')
            try:
                num = float(token)
                tokens.append(num)
            except ValueError:
                continue
        return tokens

    def parse_content(self, content: str) -> list:
        """
        Parsuje zawartość pliku LST, wyodrębniając z niego detale.
        W zależności od wersji pliku LST, detale mogą być wyodrębniane na podstawie sekcji
        (np. BEGIN_PARTS_IN_PROGRAM) lub markerów w liniach z komendami G.

        :param content: Zawartość pliku LST.
        :return: Lista obiektów Detail.
        """
        self.details = []
        current_detail = None
        in_geometry = False

        # Przyjmujemy, że geometria detalu pojawia się w sekcji START_TEXT ... STOP_TEXT w BEGIN_PROGRAMM
        for line in content.splitlines():
            line = line.strip()
            # Rozpoczęcie sekcji geometrii detalu – może być oznaczone przez START_TEXT
            if line.upper().startswith("START_TEXT"):
                # W przypadku nowej sekcji, jeśli mamy już obecny detal, zakończ go
                if current_detail:
                    self.details.append(current_detail)
                # Nazwa detalu można próbować wyłuskać z poprzednich linii lub ustawić domyślnie
                current_detail = Detail(name=f"Detail_{len(self.details) + 1}")
                in_geometry = True
                continue
            if line.upper().startswith("STOP_TEXT"):
                in_geometry = False
                # Zakończ aktualny detal
                if current_detail:
                    self.details.append(current_detail)
                    current_detail = None
                continue

            # Jeżeli jesteśmy w sekcji geometrii, przetwarzaj linie zawierające współrzędne
            if in_geometry and current_detail:
                # Przykładowe linie mogą zawierać współrzędne w postaci np. "N70X-0.249Y-2.853"
                # Użyjemy wyrażenia regularnego, aby wyłuskać wartości X i Y.
                m = re.search(r'[Xx]([-+]?\d*\.?\d+)', line)
                n = re.search(r'[Yy]([-+]?\d*\.?\d+)', line)
                if m and n:
                    try:
                        x = float(m.group(1))
                        y = float(n.group(1))
                        current_detail.add_point(x, y)
                    except ValueError:
                        pass
                else:
                    # Alternatywnie, jeżeli linia zawiera ciąg liczb, dodajemy je w parach.
                    nums = self._parse_numbers_from_line(line)
                    for i in range(0, len(nums) - 1, 2):
                        current_detail.add_point(nums[i], nums[i + 1])
        # Jeśli na końcu mamy niezamknięty detal, dodaj go.
        if current_detail:
            self.details.append(current_detail)
        return self.details

    def parse_file(self, file_path: str) -> list:
        with open(file_path, 'r', encoding='cp1250') as f:
            content = f.read()
        return self.parse_content(content)

    def save_details(self, output_dir: str, margin=10):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for idx, detail in enumerate(self.details, start=1):
            safe_name = re.sub(r'[^A-Za-z0-9_\-]', '_', detail.name)
            filename = os.path.join(output_dir, f"detail_{idx}_{safe_name}.svg")
            detail.save_to_svg(filename, margin)
            print(f"Zapisano detal {idx} do pliku: {filename}")


if __name__ == "__main__":
    # Przykład użycia parsera
    lst_filename = "mc0929n5.LST"  # Podaj nazwę lub ścieżkę do pliku LST
    output_folder = "wyniki_svg"  # Folder wyjściowy, gdzie zostaną zapisane pliki SVG

    parser = LSTParser()
    details = parser.parse_file(lst_filename)
    print(f"Znaleziono {len(details)} detali w pliku {lst_filename}.")
    for idx, det in enumerate(details, start=1):
        print(f"Detal {idx} ({det.name}): liczba punktów = {len(det.points)}")
    parser.save_details(output_folder)
