import json
from pathlib import Path
from dataclasses import dataclass

path = Path(__file__).resolve().parent / "ingredients.json"

with path.open() as fp:
    profiles = json.load(fp)

ingredientNames = list(profiles.keys())


@dataclass
class IngredientProfile:
    mass: float = 0.0
    flour: float = 0.0
    water: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0
    fiber: float = 0.0


def ingredientProfile(name: str):
    if not name in profiles:
        if name.endswith("flour"):
            name = "flour"
        elif name.endswith("water"):
            name = "water"
        elif name.endswith("oil"):
            name = "oil"
        else:
            name = "unknown"

    return IngredientProfile(**profiles[name])
