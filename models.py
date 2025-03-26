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

    def cutting_cost(self, config: dict, material: str) -> float:
        material_lower = material.lower()
        if "1.4301" in material_lower:
            rate = config.get("cutting_costs", {}).get("stal_nierdzewna", 6.0)
        elif "1.0038" in material_lower or "st37" in material_lower:
            rate = config.get("cutting_costs", {}).get("stal_czarna", 5.0)
        elif "aluminium" in material_lower:
            rate = config.get("cutting_costs", {}).get("aluminium", 4.5)
        else:
            rate = config.get("cutting_costs", {}).get("stal_czarna", 5.0)
        return round(self.cut_time * rate, 2)

    def material_cost(self, config: dict, material: str) -> float:
        material_lower = material.lower()
        if "1.4301" in material_lower:
            cost = config.get("material_costs", {}).get("stal_nierdzewna", 3.0)
        elif "1.0038" in material_lower or "st37" in material_lower:
            cost = config.get("material_costs", {}).get("stal_czarna", 2.5)
        elif "aluminium" in material_lower:
            cost = config.get("material_costs", {}).get("aluminium", 1.5)
        else:
            cost = config.get("material_costs", {}).get("stal_czarna", 2.5)
        return round(self.weight * cost, 2)

    def total_cost(self, config: dict, material: str) -> float:
        return round(self.cutting_cost(config, material) + self.material_cost(config, material), 2)

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
        details_cost = sum(detail.total_cost(config, self.material) * detail.quantity for detail in self.details)
        bending_cost = config.get("suma_kosztow_giecia", 0.0)
        return round(details_cost + bending_cost, 2)

    def add_detail(self, detail: Detail):
        self.details.append(detail)
