from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Detail:
    """Reprezentuje pojedynczy detal do wycięcia."""
    name: str
    quantity: int
    dimensions: str  # oczekiwany format, np. "60.000 x 78.000 mm"
    cut_time: float  # czas cięcia pojedynczej sztuki [minuty]
    cut_length: float  # długość cięcia [mm]
    weight: float      # waga detalu [kg]
    image_path: Optional[str] = None  # ścieżka do obrazka (BMP) detalu

    def cutting_cost(self, config: dict) -> float:
        rate_per_minute = config.get("rate_per_minute", 5.0)
        return round(self.cut_time * rate_per_minute, 2)

    def material_cost(self, config: dict) -> float:
        material_cost_per_kg = config.get("material_cost_per_kg", 2.5)
        return round(self.weight * material_cost_per_kg, 2)

    def total_cost(self, config: dict) -> float:
        return round(self.cutting_cost(config) + self.material_cost(config), 2)

@dataclass
class Program:
    """Reprezentuje cały program cięcia laserowego."""
    name: str
    material: str
    thicknes: float  # grubość materiału [mm]
    machine_time: str  # czas maszynowy jako string, np. "0:00:07"
    program_counts: int
    details: List[Detail] = field(default_factory=list)

    def total_cut_time(self) -> float:
        return sum(detail.cut_time * detail.quantity for detail in self.details)

    def total_cost(self, config: dict) -> float:
        return round(sum(detail.total_cost(config) * detail.quantity for detail in self.details), 2)

    def add_detail(self, detail: Detail):
        self.details.append(detail)
