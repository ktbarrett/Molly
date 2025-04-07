from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from molly.source import Context


@dataclass
class Token:
    context: Context


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
class ParenList:
    lparen: LParen
    exprs: list[ParenListExpr]
    rparen: RParen


ParenListExpr: TypeAlias = ParenList | Atom


@dataclass
class WSSingle:
    expr: WSElemExpr
    newline: Newline


@dataclass
class WSList:
    exprs: list[WSElemExpr]
    newline: Newline


@dataclass
class WSBlock:
    leading_exprs: list[WSElemExpr]
    newline: Newline
    indent: Indent
    block_exprs: list[WSExpr]
    dedent: Dedent


@dataclass
class CurlyList:
    lcurly: LCurly
    exprs: list[WSExpr]
    rcurly: RCurly


WSElemExpr: TypeAlias = CurlyList | ParenListExpr

WSExpr: TypeAlias = WSList | WSSingle | WSBlock


@dataclass
class Program:
    exprs: list[WSExpr]


@dataclass(repr=False)
class ParseError(Exception):
    context: Context
    message: str

    def __repr__(self) -> str:
        return f"{self.context.name}:{self.context.lineno}:{self.context.charno}: {type(self).__qualname__}: {self.message}"
