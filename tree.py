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


@dataclass
class Part(Base):
    name: str
    vars: list[Var] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)

    def addVar(self, part: str, name: str):
        v = Var(part, name)
        if v.part == self.name and v not in self.vars:
            self.vars.append(v)

    @overload
    def addRelation(self, a: str, b: str, c: Values) -> None: ...

    @overload
    def addRelation(self, a: Var, b: Values) -> None: ...

    @overload
    def addRelation(self, a: Relation) -> None: ...

    def addRelation(
        self,
        a: str | Var | Relation,
        b: str | Values | None = None,
        c: Values | None = None,
    ) -> None:

        match (a, b, c):
            case (str(part), str(name), value) if isinstance(value, Values):
                self.relations.append(Relation(Var(part, name), value))
            case (Var() as var, value, None) if isinstance(value, Values):
                self.relations.append(Relation(var, value))
            case (Relation() as r, None, None):
                self.relations.append(r)
            case _:
                raise NotImplementedError


@dataclass
class Relation(Base):
    var: Var
    value: Values
    weight: float = 1


@dataclass
class Hydration(Base):
    value: float


@dataclass
class Sum(Base):
    terms: list[Values]


@dataclass
class Product(Base):
    factors: list[Values]


@dataclass
class Divide(Base):
    lhs: Values
    rhs: float


@dataclass
class Var(Base):
    part: str
    name: str

    @property
    def t(self):
        return (self.part, self.name)


def isVar(v) -> TypeGuard[Var]:
    return isinstance(v, Var)


Values = Sum | Product | Divide | Var | float | int

Vector = NDArray[np.float64]


def isVector(v) -> TypeGuard[Vector]:
    return isinstance(v, np.ndarray)


Matrix = NDArray[np.float64]
