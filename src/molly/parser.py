from __future__ import annotations

from typing import cast

import molly.ast as ast
from molly.lexer import Lexer


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer

    def parse_program(self) -> ast.Program:
        exprs: list[ast.WSExpr] = []
        while True:
            match self._lexer.curr():
                case ast.EOF():
                    return ast.Program(exprs)
                case _:
                    expr = self._parse_ws_expr()
                    exprs.append(expr)

    def _parse_ws_expr(self) -> ast.WSExpr:
        leading_exprs: list[ast.WSElemExpr] = []
        while True:
            match self._lexer.curr():
                case ast.Newline() as newline:
                    self._lexer.next()
                    match self._lexer.curr():
                        case ast.Indent() as indent:
                            self._lexer.next()
                            exprs: list[ast.WSExpr] = []
                            while True:
                                match self._lexer.curr():
                                    case ast.Dedent() as dedent:
                                        self._lexer.next()
                                        return ast.WSBlock(
                                            leading_exprs,
                                            newline,
                                            indent,
                                            exprs,
                                            dedent,
                                        )
                                    case _:
                                        expr = self._parse_ws_expr()
                                        exprs.append(expr)
                        case _:
                            if len(leading_exprs) == 1:
                                return ast.WSSingle(leading_exprs[0], newline)
                            else:
                                return ast.WSList(leading_exprs, newline)
                case _:
                    leading_expr = self._parse_ws_elem()
                    leading_exprs.append(leading_expr)

    def _parse_ws_elem(self) -> ast.WSElemExpr:
        match self._lexer.curr():
            case ast.LCurly():
                return self._parse_curly_list()
            case ast.LParen():
                return self._parse_list_expr()
            case token if isinstance(token, ast.Atom):
                self._lexer.next()
                return token
            case _:
                raise ast.ParseError(
                    token.filename,
                    token.lineno,
                    token.charno,
                    f"Expected paren list, curly listy, or atom, got {type(token).__qualname__}",
                )

    def _parse_paren_list_elem(self) -> ast.ParenListExpr:
        match self._lexer.curr():
            case ast.LParen:
                return self._parse_list_expr()
            case token if isinstance(token, ast.Atom):
                self._lexer.next()
                return token
            case _:
                raise ast.ParseError(
                    token.filename,
                    token.lineno,
                    token.charno,
                    f"Expected paren list or atom, got {type(token).__qualname__}",
                )

    def _parse_list_expr(self) -> ast.ParenList:
        lparen = cast(ast.LParen, self._lexer.curr())
        self._lexer.next()

        exprs: list[ast.ParenListExpr] = []
        while True:
            match self._lexer.curr():
                case ast.RParen() as rparen:
                    self._lexer.next()
                    return ast.ParenList(lparen, exprs, rparen)
                case _:
                    expr = self._parse_paren_list_elem()
                    exprs.append(expr)

    def _parse_curly_list(self) -> ast.CurlyList:
        lcurly = cast(ast.LCurly, self._lexer.curr())
        self._lexer.next()

        exprs: list[ast.WSExpr] = []
        while True:
            match self._lexer.curr():
                case ast.RCurly() as rcurly:
                    self._lexer.next()
                    return ast.CurlyList(lcurly, exprs, rcurly)
                case _:
                    expr = self._parse_ws_expr()
                    exprs.append(expr)


if __name__ == "__main__":
    import sys

    from molly.source import TextIOSourceIterator

    if len(sys.argv) == 1:
        file = sys.stdin
        name = "<stdin>"
    elif len(sys.argv) == 2:
        file = open(sys.argv[1])
        name = sys.argv[1]
    else:
        raise ValueError("Too many arguments")

    source = TextIOSourceIterator(name, file)
    lexer = Lexer(source)
    parser = Parser(lexer)

    print(parser.parse_program())
