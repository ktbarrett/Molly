from __future__ import annotations

from ast import literal_eval

import molly.ast as ast
from molly.source import SourceIterator, TextIOSourceIterator


def str_range(start: str, end: str) -> set[str]:
    return {chr(c) for c in range(ord(start), ord(end) + 1)}


_numbers = str_range("0", "9")

# Numbers must start with "-" or 0-9.
# Implicit leading 0s aren't supported for starting with ".".
_number_start_chars = set("-") | _numbers

# names can't start with...
#   delimiters: " " # ( ) { } [ ]
#   quotes: ' \"
#   number start characters: "-" 0-9
#   dot: .
_name_start_chars = (
    str_range("a", "z") | str_range("A", "Z") | set("~`!@$%^&*-_=[]+|;:<,>.?/")
)

# After the start character, names can contain quotes, number start characters, and dot
_name_rest_chars = _name_start_chars | _number_start_chars | set("\"'.")


_hexchars = _numbers | set("ABCDEF")


class Lexer:
    def __init__(self, src: SourceIterator) -> None:
        self._src = src
        self._lookahead: ast.Token | None = None

    def peek(self) -> ast.Token:
        if self._lookahead is None:
            self._next()
        assert self._lookahead is not None
        return self._lookahead

    def next(self) -> ast.Token:
        res, self._lookahead = self.peek(), None
        return res

    def _emit(self, token: ast.Token) -> None:
        assert self._lookahead is None
        self._lookahead = token

    def _next(self) -> None:
        while True:
            match self._src.peek():
                case " ":
                    self._src.next()
                    continue
                case "#":
                    self._ignore_comment()
                    continue
                case "\n":
                    self._src.next()
                    continue  # TODO
                case "(":
                    return self._emit_delim(ast.LParen)
                case ")":
                    return self._emit_delim(ast.RParen)
                case "{":
                    return self._emit_delim(ast.LCurly)
                case "}":
                    return self._emit_delim(ast.RCurly)
                case c if c in _number_start_chars:
                    return self._lex_number()
                case '"':
                    return self._lex_string()
                case c if c in _name_start_chars:
                    return self._lex_name()
                case "\0":
                    return self._emit_delim(ast.EOF)
                case ".":
                    raise ast.ParseError(
                        self._src.filename,
                        self._src.lineno,
                        self._src.charno,
                        "Names can't start with '.' and Numbers must start with '-' or a digit.",
                    )
                case c:
                    breakpoint()
                    raise ast.ParseError(
                        self._src.filename,
                        self._src.lineno,
                        self._src.charno,
                        f"Source contained non-printable character: '{c}'",
                    )

    def _ignore_comment(self) -> None:
        while self._src.peek() not in "\n\0":
            self._src.next()

    def _emit_delim(self, token_cls: type[ast.Token]) -> None:
        token = token_cls(self._src.filename, self._src.lineno, self._src.charno)
        self._src.next()
        self._emit(token)

    def _lex_number(self) -> None:
        start_charno = self._src.charno
        capture: list[str] = []

        # optional starting '-'
        if self._src.peek() == "-":
            capture.append(self._src.next())

        # at least 1 number
        if self._src.peek() not in _numbers:
            raise ast.ParseError(
                self._src.filename,
                self._src.lineno,
                start_charno,
                "Invalid number literal. At least one number required in integer part.",
            )
        capture.append(self._src.next())

        # as many numbers as you want
        while self._src.peek() in _numbers:
            capture.append(self._src.next())

        is_float: bool = False

        # optional fraction
        if self._src.peek() == ".":
            is_float = True
            capture.append(self._src.next())

            # at least 1 number
            if self._src.peek() not in _numbers:
                raise ast.ParseError(
                    self._src.filename,
                    self._src.lineno,
                    start_charno,
                    "Invalid number literal. At least one number required in fractional part.",
                )
            capture.append(self._src.next())

            # as many numbers as you want
            while self._src.peek() in _numbers:
                capture.append(self._src.next())

        # optional exponent
        if self._src.peek() == "e":
            is_float = True
            capture.append(self._src.next())

            # optional starting '-'
            if self._src.peek() == "-":
                capture.append(self._src.next())

            # at least 1 number
            if self._src.peek() not in _numbers:
                raise ast.ParseError(
                    self._src.filename,
                    self._src.lineno,
                    start_charno,
                    "Invalid number literal. At least one number required in fractional part.",
                )
            capture.append(self._src.next())

            # as many numbers as you want
            while self._src.peek() in _numbers:
                capture.append(self._src.next())

        value = literal_eval("".join(capture))
        if is_float:
            self._emit(
                ast.Float(self._src.filename, self._src.lineno, start_charno, value)
            )
        else:
            self._emit(
                ast.Integer(self._src.filename, self._src.lineno, start_charno, value)
            )

    def _lex_string(self) -> None:
        start_charno = self._src.charno
        capture: list[str] = []
        assert self._src.next() == '"'
        while True:
            match self._src.peek():
                case '"':
                    self._src.next()
                    value = "".join(capture)
                    return self._emit(
                        ast.String(
                            self._src.filename, self._src.lineno, start_charno, value
                        )
                    )
                case "\\":
                    escape_start_charno = self._src.charno
                    self._src.next()
                    match self._src.peek():
                        case "n":
                            capture.append("\n")
                            self._src.next()
                        case "t":
                            capture.append("\t")
                            self._src.next()
                        case "\\":
                            capture.append("\\")
                            self._src.next()
                        case '"':
                            capture.append('"')
                            self._src.next()
                        case "x":
                            self._src.next()
                            escape_capture: list[str] = []
                            for _ in range(2):
                                if self._src.peek() not in _hexchars:
                                    raise ast.ParseError(
                                        self._src.filename,
                                        self._src.lineno,
                                        escape_start_charno,
                                        "Invalid escape sequence",
                                    )
                                escape_capture.append(self._src.next())
                            escape_value = chr(int("".join(escape_capture), 16))
                            capture.append(escape_value)
                        case c:
                            raise ast.ParseError(
                                self._src.filename,
                                self._src.lineno,
                                escape_start_charno,
                                "Invalid escape sequence",
                            )
                case c if c.isprintable():
                    capture.append(c)
                    self._src.next()
                case "\0" | "\n":
                    raise ast.ParseError(
                        self._src.filename,
                        self._src.lineno,
                        start_charno,
                        "Unterminated string literal",
                    )
                case _:
                    raise ast.ParseError(
                        self._src.filename,
                        self._src.lineno,
                        self._src.charno,
                        f"String contains non-printable character: '{c}'",
                    )

    def _lex_name(self) -> None:
        start_charno = self._src.charno
        capture: list[str] = [self._src.next()]
        while self._src.peek() in _name_rest_chars:
            capture.append(self._src.next())
        value = "".join(capture)
        match value:
            case "null":
                self._emit(ast.Null(self._src.filename, self._src.lineno, start_charno))
            case "true":
                self._emit(
                    ast.TrueToken(self._src.filename, self._src.lineno, start_charno)
                )
            case "false":
                self._emit(
                    ast.FalseToken(self._src.filename, self._src.lineno, start_charno)
                )
            case _:
                self._emit(
                    ast.Name(self._src.filename, self._src.lineno, start_charno, value)
                )


if __name__ == "__main__":
    import sys

    lexer = Lexer(TextIOSourceIterator("stdin", sys.stdin))

    while type(token := lexer.peek()) is not ast.EOF:
        print(token)
        lexer.next()
