from dataclasses import dataclass
from typing import Dict
import numpy as np
from ingredients import ingredientProfile


@dataclass
class SymbolTableEntry:
    partName: str
    ingredient: str
    index: int
    value: float = 0


class SymbolTable:
    def __init__(self):
        self.unknowns: Dict[str, SymbolTableEntry] = dict()
        self.indexToName: Dict[int, str] = dict()
        self.parts: set[str] = set()
        self.currentPart: str = ""
        self.vectorLength = 0
        # set on first call to vector
        self.totals = ["total_flour", "total_water", "total_mass"]

    @property
    def part(self):
        return self.currentPart

    @part.setter
    def part(self, name: str):
        self.currentPart = name
        if name not in self.parts:
            self.parts.add(name)

    def add(self, ingredient: str):
        if self.vectorLength > 0:
            raise RuntimeError("Toolate to add an ingredient")

        fullName = f"{self.currentPart}.{ingredient}"
        if fullName not in self.unknowns:
            entry = SymbolTableEntry(self.currentPart, ingredient, len(self.unknowns))
            self.unknowns[fullName] = entry

    def entry(self, ingredient: str, part: str = ""):
        if "." in ingredient:
            part, ingredient = ingredient.split(".")

        if not part:
            if ingredient in self.parts:
                part = ingredient
                ingredient = "total_mass"
            else:
                part = self.currentPart

        fullName = f"{part}.{ingredient}"
        return self.unknowns[fullName]

    def vector(self, ingredient: str, scale: float = 1, part: str = ""):
        if self.vectorLength == 0:
            self.vectorLength = len(self.unknowns) + 1
        col = self.entry(ingredient, part).index
        v = np.zeros(self.vectorLength)
        v[col] = scale
        return v

    def constant(self, value: float):
        v = np.zeros(self.vectorLength)
        v[-1] = value
        return v

    def value(self, ingredient: str, part: str = ""):
        return self.entry(ingredient, part).value

    def index(self, ingredient: str, part: str = ""):
        return self.entry(ingredient, part).index

    def profileVectors(self, ingredient: str):
        if ingredient in self.parts:
            part = ingredient
            return {
                "flour": self.vector("total_flour", 1, part),
                "water": self.vector("total_water", 1, part),
                "mass": self.vector("total_mass", 1, part),
            }
        profile = ingredientProfile(ingredient)
        return {
            "flour": self.vector(ingredient, profile.flour),
            "water": self.vector(ingredient, profile.water),
            "mass": self.vector(ingredient, 1),
        }

    def profileValues(self, ingredient: str):
        if ingredient in self.parts:
            part = ingredient
            return {
                "flour": self.value("total_flour", part),
                "water": self.value("total_water", part),
                "mass": self.value("total_mass", part),
            }
        profile = ingredientProfile(ingredient)
        mass = self.value(ingredient)
        return {
            "flour": mass * profile.flour,
            "water": mass * profile.water,
            "mass": mass,
        }

    def setValues(self, values: np.ndarray):
        for fullname in self.unknowns:
            entry = self.unknowns[fullname]
            entry.value = values[entry.index]
