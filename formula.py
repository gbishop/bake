import re
from typing import Any, List, TypeGuard
import numpy as np
from symbolTable import SymbolTable


def isNumber(val: Any) -> TypeGuard[float]:
    """Helper equivalent to JS isNumber check."""
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def isVector(val: Any) -> TypeGuard[np.ndarray]:
    return isinstance(val, np.ndarray)


class FormulaError(Exception):
    """Custom exception raised during expression tokenization or parsing."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.msg = message
        self.row: int = 0
        self.prop: str = "formula"


def formulaV(st: SymbolTable, expr: str, local_percent: bool = False) -> np.ndarray:
    """Evaluate a formula producing a Vector."""
    ee = ExpressionEvaluator(st, local_percent=local_percent, use_values=False)
    v = ee.evaluate(expr)
    if isNumber(v):
        return st.constant(v)
    return v


def formulaN(st: SymbolTable, expr: str, local_percent: bool = False) -> float:
    """Evaluate a formula producing a raw number."""
    ee = ExpressionEvaluator(st, local_percent=local_percent, use_values=True)
    v = ee.evaluate(expr)
    if not isNumber(v):
        raise FormulaError("formula_n should return a number")
    return float(v)


class ExpressionEvaluator:
    # 1. Base pattern blocks
    _NUM_BASE = r"\d+(?:\.\d+)?(?:e[+-]?\d+)?"
    _SUFFIXES = r"g|%|ppm|pf|pw|pm"
    _ID_PATTERN = r"[a-zA-Z_][a-zA-Z0-9_.]*"
    _OP_PATTERN = r"[\+\-\*\/\(\)]"

    # 2. Compiled constants built from base blocks
    _NUM_RE = re.compile(rf"^({_NUM_BASE})({_SUFFIXES})?$")
    _ID_RE = re.compile(rf"^{_ID_PATTERN}$")
    _TOKEN_RE = re.compile(rf"{_NUM_BASE}(?:{_SUFFIXES})?|{_ID_PATTERN}|{_OP_PATTERN}")
    _PERCENT_MAP = {
        "%": "total_flour",
        "pf": "total_flour",
        "pw": "total_water",
        "pm": "total_mass",
    }

    def __init__(
        self, st: SymbolTable, local_percent: bool = False, use_values: bool = False
    ) -> None:
        self.st = st
        self.local_percent = local_percent
        self.use_values = use_values
        self.tokens: List[str] = []
        self.index: int = 0

    def evaluate(self, expression: str) -> Any:
        self.tokens = self._TOKEN_RE.findall(expression)
        self.index = 0
        result = self.parse_expression()

        if self.index < len(self.tokens):
            raise FormulaError(f"Unexpected token: {self.tokens[self.index]}")
        return result

    def parse_expression(self) -> Any:
        """Handle + and -"""
        left = self.parse_term()
        while self.match("+") or self.match("-"):
            op = self.tokens[self.index - 1]
            right = self.parse_term()
            left = self.execute_op(op, left, right)
        return left

    def parse_term(self) -> Any:
        """Handle * and /"""
        left = self.parse_factor()
        while self.match("*") or self.match("/"):
            op = self.tokens[self.index - 1]
            right = self.parse_factor()
            left = self.execute_op(op, left, right)
        return left

    def parse_factor(self) -> Any:
        """Handle unary minus, parentheses, numbers, and variables."""
        if self.match("-"):
            result = self.parse_factor()
            return self.execute_op("-", 0, result)

        if self.match("("):
            result = self.parse_expression()
            if not self.match(")"):
                raise FormulaError("Missing closing parenthesis")
            return result

        if self.index >= len(self.tokens):
            raise FormulaError("Unexpected end of expression")

        token = self.tokens[self.index]

        # numbers
        if match := self._NUM_RE.match(token):
            number, suffix = match.groups()
            self.index += 1
            return self._apply_suffix(float(number), suffix)

        # variables
        if self._ID_RE.match(token):
            self.index += 1
            try:
                if self.use_values:
                    return self.st.value(token)
                return self.st.vector(token)
            except KeyError:
                raise FormulaError(f"Undefined symbol {token}")

        raise FormulaError(f"Unexpected token: {token}")

    def _apply_suffix(self, value: float, suffix: str | None) -> Any:
        """Processes unit suffixes and converts values or symbol references."""
        if not suffix or suffix == "g":
            return value

        if suffix == "ppm":
            return value * 1e-6

        if target_symbol := self._PERCENT_MAP.get(suffix):
            scale = value / 100.0
            scope = ("" if self.local_percent else "dough") if suffix == "%" else None
            return self._scaled_symbol(target_symbol, scale, scope)

        return value

    def _scaled_symbol(
        self, symbol: str, scale: float, scope: str | None = None
    ) -> Any:
        """Helper to fetch value vs vector across symbol table calls DRYly."""
        if self.use_values:
            val = self.st.value(symbol, scope) if scope else self.st.value(symbol)
            return scale * val
        return (
            self.st.vector(symbol, scale, scope)
            if scope is not None
            else self.st.vector(symbol, scale)
        )

    def match(self, token: str) -> bool:
        if self.index < len(self.tokens) and self.tokens[self.index] == token:
            self.index += 1
            return True
        return False

    def execute_op(self, op: str, a: np.ndarray | float, b: np.ndarray | float) -> Any:
        if op == "+":
            if isNumber(a):
                if isNumber(b):
                    return a + b
                elif isVector(b):
                    r = b.copy()
                    r[-1] += a
                    return r
            elif isVector(a) and isNumber(b):
                r = a.copy()
                r[-1] += b
                return r
            else:
                return a + b

        if op == "-":
            if isNumber(a):
                if isNumber(b):
                    return a - b
                elif isVector(b):
                    r = -b
                    r[-1] += a
                    return r
            elif isVector(a) and isNumber(b):
                r = a.copy()
                r[-1] -= b
                return r
            else:
                return a + b

        if op == "*":
            if isNumber(a) or isNumber(b):
                return a * b
            else:
                raise FormulaError("Cannot multiply two unknowns.")

        if op == "/":
            if isNumber(b):
                return a / b
            raise FormulaError("Division of unknowns is not supported")

        raise FormulaError(f"Invalid operation {a} {op} {b}")


if __name__ == "__main__":
    st = SymbolTable()
    st.add("x")
    st.add("y")
    st.setValues(np.array([2, 3]))

    v = formulaN(st, "x + y * 2.5ppm")
    print(v)
