import re
from models import Program, Detail
from pdf_utils import find_field, find_in_section, extract_all_detail_images


def parse_pdf_new(doc, full_text: str) -> Program:
    try:
        # Debug – wypisanie numeracji linii dokumentu
        print("=== Numeracja linii dokumentu ===")
        for i, line in enumerate(full_text.splitlines(), start=1):
            print(f"{i}: {line}")
        print("=== Koniec numeracji linii dokumentu ===")

        # --- 1. Nazwa programu
        prog_name_match = re.search(r"Liczba detali:\s*Liczba arkuszy:\s*\n\s*(\S+)", full_text,
                                    re.IGNORECASE | re.MULTILINE)
        if prog_name_match:
            program_name = prog_name_match.group(1).strip()
        else:
            program_name = ""

        # --- 2. Ilość powtórzeń programu – pobieramy z sekcji "Czas trwania"
        rep_match = re.search(r"Czas\s+trwania\s*\n\s*(\S+)\s+(\d+)", full_text, re.IGNORECASE | re.MULTILINE)
        if rep_match:
            program_counts = int(rep_match.group(2))
        else:
            program_counts = 0

        # --- 3. Rodzaj materiału – szukamy ciągu odpowiadającego schematowi:
        # np. "ST0M0300----3000x1500 (1.0038)"
        mat_match = re.search(r"[A-Z0-9]+----[0-9x]+\s*\((\d+\.\d+)\)", full_text, re.IGNORECASE)
        if mat_match:
            material = mat_match.group(1).strip()
        else:
            material = ""

        # --- 3b. Grubość materiału – pobieramy z linii po "Wymiary:"
        dims_match = re.search(r"Wymiary:\s*\n\s*(.+)", full_text, re.IGNORECASE | re.MULTILINE)
        if dims_match:
            dims_full = dims_match.group(1).strip()  # np. "3000,00 x 1500,00 x 3,00 mm"
            parts = dims_full.split("x")
            if parts:
                # Pobieramy ostatni fragment, usuwamy jednostki, zamieniamy przecinek na kropkę
                last_part = parts[-1].strip().split()[0].replace(",", ".")
                try:
                    thicknes = abs(float(last_part))
                except Exception:
                    thicknes = 0.0
            else:
                thicknes = 0.0
        else:
            thicknes = 0.0

        # --- 4. Czas trwania maszyny – usuwamy część w nawiasach kwadratowych, np. "[h:min:s]"
        machine_time = find_field(full_text, "Czas trwania")
        machine_time = re.sub(r"\s*\[.*\]", "", machine_time).strip()

        print("Nowy PDF:")
        print("1. Nazwa programu:", program_name)
        print("2. Rodzaj materiału (z nawiasu):", material)
        print("3. Czas trwania:", machine_time)
        print("4. Ilość powtórzeń programu:", program_counts)
        print("5. GRUBOŚĆ:", thicknes)

        # --- 5. Parsowanie sekcji detali
        if "Informacja o pojedynczych detalach/zleceniu" in full_text:
            detail_block = full_text.split("Informacja o pojedynczych detalach/zleceniu", 1)[1].strip()
        else:
            detail_block = ""

        detail_parts = re.split(r"\n\s*\n", detail_block)
        if len(detail_parts) < 4:
            print("Nie udało się poprawnie podzielić sekcji detali.")
            details = []
        else:
            # Segment 1: wartości pierwszej grupy (np. Plik geo, Wymiary)
            values_part_1 = detail_parts[1].strip().splitlines()
            # Segment 2: wartości drugiej grupy (np. Szt., Czas obróbki detalu)
            values_part_2 = detail_parts[3].strip().splitlines()

            if len(values_part_1) >= 5:
                det_name = values_part_1[3].strip()
                dims_str = values_part_1[4].strip()
                dims_parts = dims_str.split("x")
                if len(dims_parts) >= 2:
                    dim_x = dims_parts[0].strip()
                    dim_y = dims_parts[1].strip().split()[0]
                else:
                    dim_x = dims_str
                    dim_y = ""
            else:
                det_name = ""
                dims_str = ""
                dim_x = ""
                dim_y = ""

            if len(values_part_2) >= 3:
                try:
                    quantity = int(values_part_2[0].strip())
                except ValueError:
                    quantity = 1
                cut_time = values_part_2[2].strip()  # np. "00:00:03"
            else:
                quantity = 1
                cut_time = "0"

            details = []
            images = extract_all_detail_images(doc)
            image_path = images[0] if images else None

            print("Detail 1 (nowy PDF):")
            print("   Plik geo (nazwa detalu):", det_name)
            print("   Wymiary: x =", dim_x, ", y =", dim_y)
            print("   Czas obróbki detalu:", cut_time)
            print("   Szt. (ilość):", quantity)
            print("   Rodzaj materiału (dla detalu):", material)
            print("   GRUBOŚĆ:", thicknes)

            detail = Detail(
                name=det_name,
                quantity=quantity,
                dimensions=dims_str,  # np. f"{dim_x} x {dim_y}"
                cut_time=cut_time,
                cut_length=0.0,
                weight=0.0,
                image_path=image_path
            )
            details.append(detail)

        program = Program(
            name=program_name,
            material=material,  # rodzaj materiału
            thicknes=thicknes,
            machine_time=machine_time,
            program_counts=program_counts,
            details=details
        )
        print("Program (nowy PDF):", program)
        return program

    except Exception as e:
        print("Wystąpił błąd w parse_pdf_new:", e)
        return Program(name="", material="", thicknes=0.0, machine_time="", program_counts=0, details=[])
