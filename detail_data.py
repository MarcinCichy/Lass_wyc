"""
Moduł do wyciągania danych o poszczególnych detalach z danych programu.
Obsługuje zarówno pliki HTML (obiekty BeautifulSoup) jak i LST (lista słowników).
"""

import ntpath
from parser_dispatcher import get_program_data


class Detail:
    def __init__(self, name, material, thickness, dimension_x, dimension_y, element_cut_time, quantity, index):
        self.name = name
        self.material = material
        self.thickness = thickness
        self.dimension_x = dimension_x
        self.dimension_y = dimension_y
        self.element_cut_time = element_cut_time
        self.quantity = quantity
        self.index = index

    def element_cut_cost(self):
        cut_hour_price = 420  # Cena za godzinę cięcia
        return round(cut_hour_price * (self.element_cut_time / 60), 2)

    def element_material_cost(self):
        material_weight = 2.8  # Przykładowa wartość (kg/m²)
        material_price = 15    # Cena materiału za kg
        if self.thickness <= 5:
            dx = dy = 10
        elif self.thickness <= 10:
            dx = dy = 20
        else:
            dx = dy = 2 * self.thickness
        dimX_brutto = (self.dimension_x + dx) / 1000
        dimY_brutto = (self.dimension_y + dy) / 1000
        return round(dimX_brutto * dimY_brutto * material_weight * self.thickness * material_price, 2)

    def total_detail_cost(self):
        return round(self.element_cut_cost() + self.element_material_cost(), 2)

    def quantity_total_cost(self):
        return round(self.total_detail_cost() * self.quantity, 2)

    def show_element_datas(self):
        print(f"Nazwa detalu: {self.name}")
        print(f"Materiał: {self.material}")
        print(f"Grubość: {self.thickness} mm")
        print(f"Wymiar X: {self.dimension_x} mm")
        print(f"Wymiar Y: {self.dimension_y} mm")
        print(f"Czas cięcia detalu: {self.element_cut_time} min")
        print(f"Ilość: {self.quantity}")

    def show_element_costs(self):
        print(f"Koszt cięcia: {self.element_cut_cost()} zł netto/szt.")
        print(f"Koszt materiału: {self.element_material_cost()} zł netto/szt.")
        print(f"Całkowity koszt jednego detalu: {self.total_detail_cost()} zł netto/szt.")
        if self.quantity > 1:
            print(f"Koszt {self.quantity} detali: {self.quantity_total_cost()} zł netto.")


def get_element_data(file_path):
    program = get_program_data(file_path)
    details = []
    rows = program.details_table_rows
    if not rows:
        return details

    if isinstance(rows[0], dict):
        index = 0
        for mapping in rows:
            if "Geometriefilename (einf.Darstl)" in mapping:
                name = ntpath.basename(mapping["Geometriefilename (einf.Darstl)"])
            elif "Geometriefilename" in mapping:
                name = ntpath.basename(mapping["Geometriefilename"])
            else:
                name = "brak"
            name = ntpath.splitext(name)[0]  # usuwa rozszerzenie (np. ".geo")
            try:
                quantity = int(mapping.get("Anzahl", "0"))
            except ValueError:
                quantity = 0
            try:
                element_cut_time = float(mapping.get("Bearbeitungszeit", "0"))
            except ValueError:
                element_cut_time = 0.0
            try:
                dimension_x = float(mapping.get("Abmessung X", "0"))
            except ValueError:
                dimension_x = 0.0
            try:
                dimension_y = float(mapping.get("Abmessung Y", "0"))
            except ValueError:
                dimension_y = 0.0

            detail = Detail(name, program.material, program.thickness,
                            dimension_x, dimension_y, element_cut_time,
                            quantity, index)
            details.append(detail)
            index += 1
    else:
        index = 0
        i = 0
        while i < len(rows):
            cells = rows[i].find_all("td")
            if len(cells) >= 2 and cells[1].get_text(strip=True).upper() == "NUMER CZĘŚCI:":
                block = rows[i:i+15]
                detail_dict = {}
                for row in block:
                    tds = row.find_all("td")
                    if len(tds) < 2:
                        continue
                    key = tds[0].get_text(strip=True).upper()
                    value = tds[1].get_text(strip=True)
                    detail_dict[key] = value
                name = ntpath.basename(detail_dict.get("NAZWA PLIKU GEO:", ""))
                name = ntpath.splitext(name)[0]
                try:
                    quantity = int(detail_dict.get("ILOŚĆ:", "0"))
                except ValueError:
                    quantity = 0
                dimensions = detail_dict.get("WYMIARY:", "")
                dimension_x = 0.0
                dimension_y = 0.0
                if "x" in dimensions.lower():
                    try:
                        parts = dimensions.lower().split("x")
                        dimension_x = float(parts[0].strip())
                        dimension_y = float(parts[1].strip().split()[0])
                    except ValueError:
                        pass
                try:
                    element_cut_time = float(detail_dict.get("CZAS OBRÓBKI:", "0")[:5])
                except ValueError:
                    element_cut_time = 0.0
                detail = Detail(name, program.material, program.thickness,
                                dimension_x, dimension_y, element_cut_time,
                                quantity, index)
                details.append(detail)
                index += 1
                i += 15
            else:
                i += 1
    return details
