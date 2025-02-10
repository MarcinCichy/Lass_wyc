"""
Moduł definiujący wspólny model danych dla programu.
"""


class ProgramData:
    def __init__(self, program_name="", material="", thickness=0,
                 program_time="", program_counts="", details_table_rows=None):
        self.program_name = program_name      # np. "mc2809"
        self.material = material              # np. "1.4301" (po przetworzeniu)
        self.thickness = thickness            # np. 5.0 (mm)
        self.program_time = program_time      # np. "2.46 min"
        self.program_counts = program_counts  # np. "1"
        self.details_table_rows = details_table_rows or []  # Lista – dla HTML: obiekty BS4, dla LST: lista słowników
