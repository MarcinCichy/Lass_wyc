import os
import csv


def extract_geo_data_from_lst(lst_filename):
    """
    Wczytuje plik LST (w kodowaniu cp1250) i wyszukuje w nim sekcję BEGIN_PARTS_IN_PROGRAM.
    Zbiera kolejne linie zaczynające się od "DA," lub "*", łączy linie kontynuacyjne i zwraca listę
    bloków tekstowych – każdy odpowiada jednemu rekordowi dotyczącym geometrii.
    """
    with open(lst_filename, 'r', encoding='cp1250') as f:
        lines = f.readlines()

    in_section = False
    da_blocks = []
    current_block = []
    for line in lines:
        if "BEGIN_PARTS_IN_PROGRAM" in line:
            in_section = True
            continue
        if "ENDE_PARTS_IN_PROGRAM" in line:
            in_section = False
            break
        if in_section:
            line = line.rstrip("\n")
            if line.startswith("DA,") or line.startswith("*"):
                if line.startswith("DA,") and current_block:
                    da_blocks.append(" ".join(current_block))
                    current_block = []
                # Jeśli linia zaczyna się od "*" – usuń znak "*" i ewentualne spacje
                if line.startswith("*"):
                    line = line.lstrip("*").strip()
                current_block.append(line)
    if current_block:
        da_blocks.append(" ".join(current_block))
    return da_blocks


def parse_da_block(da_block):
    """
    Parsuje pojedynczy blok (ciąg linii) zawierający rekord DA.
    Wykorzystuje csv.reader do podziału rekordu na pola.
    """
    if da_block.startswith("DA,"):
        da_block = da_block[3:]
    reader = csv.reader([da_block], delimiter=',', skipinitialspace=True)
    fields = next(reader)
    fields = [field.strip().strip("'") for field in fields]
    return fields


def generate_geo_file_content(fields):
    """
    Na podstawie listy pól (pobranych z rekordu DA) generuje przykładową treść pliku GEO.

    UWAGA: Poniższy szablon jest przykładowy – należy go dostosować do Twoich wymagań.
    """
    # Wyszukujemy nazwę pliku GEO – pierwsze pole kończące się na ".GEO"
    geo_filename = None
    for f in fields:
        if f.upper().endswith(".GEO"):
            geo_filename = os.path.basename(f)
            break
    if not geo_filename:
        geo_filename = "unknown.GEO"

    # Przykładowe pobranie kilku danych – indeksy należy dopasować do Twojego formatu DA
    try:
        length = float(fields[8])
    except:
        length = 3049.25
    try:
        sheet_x = float(fields[12])
        sheet_y = float(fields[13])
    except:
        sheet_x = 54.09
        sheet_y = 75.0
    try:
        laser_x = float(fields[15])
        laser_y = float(fields[16])
    except:
        laser_x = 22.23
        laser_y = 37.5

    content = f"""#~1
1.03
2
29.09.2020
0.000000000 0.000000000 0.000000000
{sheet_x:0.9f} {sheet_y:0.9f} 0.000000000
{length:0.9f}
1
0.001000000
0
1
##~~
#~11

none
AC1024
*BELEGT*

0.000000000



0
0
0
0
1
0
0
0
0

##~~
#~END
#~3

LASER

0.000000000 0.000000000 1.000000000
1.000000000 0.000000000 0.000000000 0.000000000
0.000000000 1.000000000 0.000000000 0.000000000
0.000000000 0.000000000 1.000000000 0.000000000
0.000000000 0.000000000 0.000000000 1.000000000
0.000000000 0.000000000 0.000000000
{sheet_x:0.9f} {sheet_y:0.9f} 0.000000000
{laser_x:0.9f} {laser_y:0.9f} 0.000000000
{length:0.9f}
0
##~~
#~30
ANSI_CODEPAGE@1250
AUFTR@*BELEGT*
BEARB@AC1024
DREHINKR@90
PART_NESTFITTYPE@2
PART_VERSION@3
PRIOFRGEO@5
ROTALLOWED@0
TKUND@none
TMUSTER@0
#~TTINFO_END
#~31
P
1
0.000000000 0.000000000 0.000000000
|~
P
2
{sheet_x:0.9f} {sheet_y:0.9f} 0.000000000
|~
##~~
#~33

1 24 0
0
0.000000000 0.000000000 1.000000000
0.000000000 0.000000000 0.000000000
{sheet_x:0.9f} {sheet_y:0.9f} 0.000000000
{laser_x:0.9f} {laser_y:0.9f} 0.000000000
{length:0.9f}
0
##~~
#~331
#~KONT_END
#~END
#~EOF
"""
    return geo_filename, content


def extract_geo_files(lst_filename, output_dir):
    """
    Główna funkcja, która:
      - wczytuje plik LST,
      - wyodrębnia rekordy DA dotyczące geometrii,
      - dla każdego rekordu generuje plik GEO i zapisuje go do output_dir.
    """
    da_blocks = extract_geo_data_from_lst(lst_filename)
    for block in da_blocks:
        fields = parse_da_block(block)
        geo_filename, geo_content = generate_geo_file_content(fields)
        print(geo_filename)
        print(output_dir)
        output_path = os.path.join(output_dir, geo_filename)
        with open(output_path, "w", encoding="cp1250") as f:
            f.write(geo_content)

def main(lst_filename=None, output_dir=None):
    extract_geo_files(lst_filename, output_dir)

if __name__ == "__main__":
    main()