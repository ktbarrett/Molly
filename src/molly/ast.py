from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass
class Token:
    filename: str
    lineno: int
    charno: int


@dataclass
class Name(Token):
    value: str


@dataclass
class Integer(Token):
    value: int


@dataclass
class Float(Token):
    value: float


@dataclass
class String(Token):
    value: str


@dataclass
class LParen(Token): ...


@dataclass
class RParen(Token): ...


@dataclass
class LCurly(Token): ...


@dataclass
class RCurly(Token): ...


@dataclass
class Newline(Token): ...


@dataclass
class Indent(Token): ...


@dataclass
class Dedent(Token): ...


@dataclass
class TrueToken(Token): ...


@dataclass
class FalseToken(Token): ...


@dataclass
class Null(Token): ...


@dataclass
class EOF(Token): ...


Atom: TypeAlias = Name | Integer | Float | String | TrueToken | FalseToken | Null


@dataclass
class ListExpr:
    lparen: LParen
    exprs: list[ListExprElem]
    rparen: RParen


ListExprElem: TypeAlias = ListExpr | Atom


@dataclass
class SpaceLineExpr:
    exprs: list[Expr]
    newline: Newline


@dataclass
class SpaceBlockExpr:
    leading_exprs: list[Expr]
    indent: Indent
    block_exprs: list[Expr]
    dedent: Dedent


@dataclass
class CurlyExpr:
    lcurly: LCurly
    exprs: list[Expr]
    rcurly: RCurly


Expr: TypeAlias = ListExpr | SpaceLineExpr | SpaceBlockExpr | CurlyExpr | Atom


@dataclass
class Program:
    exprs: list[Expr]


@dataclass(repr=False)
class ParseError(Exception):
    filename: str
    lineno: int
    charno: int
    message: str

    def __repr__(self) -> str:
        return f"{self.filename}:{self.lineno}:{self.charno}: {type(self).__qualname__}: {self.message}"
