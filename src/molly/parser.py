from __future__ import annotations

from typing import cast

import molly.ast as ast
from molly.lexer import Lexer


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer

    def parse_program(self) -> ast.Program:
        exprs: list[ast.Expr] = []
        while True:
            match type(self._lexer.curr()):
                case ast.EOF:
                    break
                case _:
                    expr = self.parse_expr()
                    exprs.append(expr)

        return ast.Program(exprs)

    def parse_expr(self) -> ast.Expr:
        match self._lexer.curr():
            case ast.LParen:
                return self._parse_list_expr()
            case ast.LCurly:
                return self._parse_curly_expr()
            case _:
                return self._parse_space_expr()

    def _parse_list_expr_elem(self) -> ast.ListExprElem:
        match type(token := self._lexer.curr()):
            case ast.LParen:
                return self._parse_list_expr()
            case ast.Atom:
                self._lexer.next()
                return cast(ast.Atom, token)
            case _:
                raise ast.ParseError(
                    token.filename,
                    token.lineno,
                    token.charno,
                    f"Expected list or atom, got {type(token).__qualname__}",
                )

    def _parse_list_expr(self) -> ast.ListExpr:
        lparen = cast(ast.LParen, self._lexer.next())

        exprs: list[ast.ListExprElem] = []
        while True:
            match type(self._lexer.curr()):
                case ast.RParen:
                    rparen = cast(ast.RParen, self._lexer.next())
                    return ast.ListExpr(lparen, exprs, rparen)
                case _:
                    expr = self._parse_list_expr_elem()
                    exprs.append(expr)

    def _parse_curly_expr(self) -> ast.CurlyExpr:
        lcurly = cast(ast.LCurly, self._lexer.next())

        exprs: list[ast.Expr] = []
        while True:
            match type(self._lexer.curr()):
                case ast.RCurly:
                    rcurly = cast(ast.RCurly, self._lexer.next())
                    return ast.CurlyExpr(lcurly, exprs, rcurly)
                case _:
                    expr = self._parse_list_expr_elem()
                    exprs.append(expr)

    def _parse_space_expr(self) -> ast.SpaceLineExpr | ast.SpaceBlockExpr:
        exprs: list[ast.Expr] = []
        while True:
            match type(self._lexer.curr()):
                case ast.Nodent:
                    newline = cast(ast.Nodent, self._lexer.next())
                    return ast.SpaceLineExpr(exprs, newline)
                case ast.Indent:
                    leading_exprs = exprs
                    indent = cast(ast.Indent, self._lexer.next())
                    block_exprs: list[ast.Expr] = []
                    while True:
                        match type(self._lexer.curr()):
                            case ast.Dedent:
                                dedent = cast(ast.Dedent, self._lexer.next())
                                return ast.SpaceBlockExpr(
                                    leading_exprs, indent, block_exprs, dedent
                                )
                            case _:
                                expr = self.parse_expr()
                                block_exprs.append(expr)
                case _:
                    expr = self.parse_expr()
                    exprs.append(expr)
