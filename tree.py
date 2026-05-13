"""
Data classes for my recipe AST
"""

from __future__ import annotations
from dataclasses import dataclass, fields, replace, field
from typing import TypeGuard, Iterable, overload
import numpy as np
from numpy.typing import NDArray


@dataclass
class Base:
    def walk(self):
        yield self

        for f in fields(self):
            value = getattr(self, f.name)

            if isinstance(value, Base):
                yield from value.walk()

            elif isinstance(value, Iterable):
                for item in value:
                    if isinstance(item, Base):
                        yield from item.walk()

    def map(self, transform_func):
        changes = {}
        for f in fields(self):
            val = getattr(self, f.name)

            if isinstance(val, Base):
                # If a single child returns None, we store None
                changes[f.name] = val.map(transform_func)

            elif isinstance(val, (list, tuple)):
                # Filter out None values returned by children
                new_items = []
                for item in val:
                    transformed = (
                        item.map(transform_func) if isinstance(item, Base) else item
                    )
                    if transformed is not None:  # <--- THE FILTER
                        new_items.append(transformed)

                changes[f.name] = type(val)(new_items)

        # Reconstruct the node
        new_node = replace(self, **changes)

        # Finally, ask the transform_func if THIS node should exist
        replacement_node = transform_func(new_node)
        return replacement_node


@dataclass
class Start(Base):
    parts: tuple[Part, ...]

    def vars(self):
        return [v for part in self.parts for v in part.vars]


@dataclass
class Part(Base):
    name: str
    vars: list[Var] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)

    def __post_init__(self):
        self.addVar("total_flour")
        self.addVar("total_water")
        self.addVar("total")

    def addVar(self, name: str):
        v = Var(self.name, name)
        if v not in self.vars:
            self.vars.append(v)
        return v

    def addRelation(self, r: Relation) -> None:
        self.relations.append(r)


@dataclass
class Relation(Base):
    var: Var
    value: Values
    weight: float = 1


@dataclass
class Sum(Base):
    lhs: Values = 0.0
    rhs: Values = 0.0

    def __add__(self, value: Values):
        return Sum(self, value)


@dataclass
class Difference(Base):
    lhs: Values = 0.0
    rhs: Values = 0.0


@dataclass
class Product(Base):
    lhs: Values
    rhs: Values


@dataclass
class Var(Base):
    part: str
    name: str

    @property
    def t(self):
        return (self.part, self.name)

    def __mul__(self, scale: float):
        if scale == 0.0:
            return 0.0
        elif scale == 1.0:
            return self
        return Product(scale, self)

    def __rmul__(self, scale: float):
        if scale == 0.0:
            return 0.0
        elif scale == 1.0:
            return self
        return Product(scale, self)


def isVar(v) -> TypeGuard[Var]:
    return isinstance(v, Var)


def isFloat(v) -> TypeGuard[float]:
    return isinstance(v, (float, int))


Values = Sum | Difference | Product | Var | float | int

Vector = NDArray[np.float64]


def isVector(v) -> TypeGuard[Vector]:
    return isinstance(v, np.ndarray)


Matrix = NDArray[np.float64]


def format(value: Values | Relation) -> str:
    match value:
        case Var() as v:
            return f"{v.part}.{v.name}"
        case Product() as p:
            factors = []
            for factor in [p.lhs, p.rhs]:
                if isinstance(factor, Sum):
                    factors.append(f"({format(factor)})")
                else:
                    factors.append(format(factor))
            return " * ".join(factors)
        case Sum() as s:
            return f"{format(s.lhs)} + {format(s.rhs)}"
        case Difference() as s:
            return f"{format(s.lhs)} - {format(s.rhs)}"
        case Relation() as r:
            return f"{format(r.var)} = {format(r.value)}"
        case float() | int():
            return f"{value:.3g}"
