from __future__ import annotations

from ast import literal_eval
from collections import deque
from enum import Enum, auto

import molly.ast as ast
from molly.source import SourceIterator, _TextIOSourceIterator


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
    class _State(Enum):
        START = auto()
        RUNNING = auto()
        FINISHED = auto()

    def __init__(self, src: SourceIterator) -> None:
        self._src = src
        self._lookahead = deque[ast.Token]()
        self._paren_depth: int = 0
        self._indentation: list[list[int]] = []
        self._state: Lexer._State = Lexer._State.START

    def curr(self) -> ast.Token:
        if not self._lookahead:
            self._next()
        return self._lookahead[0]

    def next(self) -> None:
        self._lookahead.popleft()

    def _next(self) -> None:
        if self._state == self._State.START:
            self._enter_new_indentation_context()
            self._state = self._State.RUNNING
        assert self._state != self._State.FINISHED
        while True:
            match self._src.curr():
                case " ":
                    self._src.next()
                    continue
                case "#":
                    self._ignore_comment()
                    continue
                case "\n":
                    self._src.next()

                    # Inside parens newlines are just whitespace
                    if self._paren_depth > 0:
                        continue

                    # Consume whitespace until code if found so we can set indentation
                    self._run_to_next_code()
                    if self._src.curr() == "\0":
                        continue

                    # Handle closing curly bracket
                    if self._src.curr() == "}":
                        if len(self._indentation) == 1:
                            raise ast.ParseError(
                                self._src.name,
                                self._src.lineno,
                                self._src.charno,
                                "Unmatched '}'",
                            )
                        self._indentation.pop()
                        self._emit_here(ast.RCurly)
                        return self._src.next()

                    # Determine INDENT, DEDENT, NODENT.
                    curr_indentation_scope = self._indentation[-1]
                    if self._src.charno == curr_indentation_scope[-1]:
                        return self._emit_here(ast.Nodent)
                    elif self._src.charno > curr_indentation_scope[-1]:
                        curr_indentation_scope.append(self._src.charno)
                        return self._emit_here(ast.Indent)
                    else:
                        while self._src.charno < curr_indentation_scope[-1]:
                            curr_indentation_scope.pop()
                            self._emit_here(ast.Dedent)
                        return
                case "(":
                    self._paren_depth += 1
                    self._emit_here(ast.LParen)
                    return self._src.next()
                case ")":
                    self._paren_depth -= 1
                    if self._paren_depth < 0:
                        raise ast.ParseError(
                            self._src.name,
                            self._src.lineno,
                            self._src.charno,
                            "Unmatched ')'",
                        )
                    self._emit_here(ast.RParen)
                    return self._src.next()
                case "{":
                    self._emit_here(ast.LCurly)
                    self._src.next()
                    self._enter_new_indentation_context()
                    return
                case "}":
                    if len(self._indentation) == 1:
                        raise ast.ParseError(
                            self._src.name,
                            self._src.lineno,
                            self._src.charno,
                            "Unmatched '}'",
                        )
                    self._indentation.pop()
                    self._emit_here(ast.RCurly)
                    return self._src.next()
                case c if c in _number_start_chars:
                    return self._lex_number()
                case '"':
                    return self._lex_string()
                case c if c in _name_start_chars:
                    return self._lex_name()
                case "\0":
                    if self._paren_depth:
                        raise ast.ParseError(
                            self._src.name,
                            self._src.lineno,
                            self._src.charno,
                            "Unterminated '( )' list",
                        )
                    if len(self._indentation) > 1:
                        raise ast.ParseError(
                            self._src.name,
                            self._src.lineno,
                            self._src.charno,
                            "Unterminated '{ }' list",
                        )
                    # emit any remaining Dedents and EOF
                    curr_indentation_scope = self._indentation[-1]
                    while len(curr_indentation_scope) > 1:
                        curr_indentation_scope.pop()
                        self._emit_here(ast.Dedent)
                    self._emit_here(ast.EOF)
                    self._state = self._State.FINISHED
                    return
                case ".":
                    raise ast.ParseError(
                        self._src.name,
                        self._src.lineno,
                        self._src.charno,
                        "Names can't start with '.' and Numbers must start with '-' or a digit.",
                    )
                case c:
                    raise ast.ParseError(
                        self._src.name,
                        self._src.lineno,
                        self._src.charno,
                        f"Source contained non-printable character: '{c}'",
                    )

    def _run_to_next_code(self) -> None:
        while True:
            while self._src.curr() in " \n":
                self._src.next()
            if self._src.curr() == "#":
                self._ignore_comment()
            else:
                break

    def _enter_new_indentation_context(self) -> None:
        self._run_to_next_code()
        if self._src.curr() == "\0":
            return
        self._indentation.append([self._src.charno])

    def _ignore_comment(self) -> None:
        while self._src.curr() not in "\n\0":
            self._src.next()

    def _emit(self, token: ast.Token) -> None:
        self._lookahead.append(token)

    def _emit_here(self, token_cls: type[ast.Token]) -> None:
        token = token_cls(self._src.name, self._src.lineno, self._src.charno)
        self._emit(token)

    def _lex_number(self) -> None:
        start_charno = self._src.charno
        capture: list[str] = []

        # optional starting '-'
        if (c := self._src.curr()) == "-":
            capture.append(c)
            self._src.next()

        # at least 1 number
        if (c := self._src.curr()) not in _numbers:
            raise ast.ParseError(
                self._src.name,
                self._src.lineno,
                start_charno,
                "Invalid number literal. At least one number required in integer part.",
            )
        capture.append(c)
        self._src.next()

        # as many numbers as you want
        while (c := self._src.curr()) in _numbers:
            capture.append(c)
            self._src.next()

        is_float: bool = False

        # optional fraction
        if (c := self._src.curr()) == ".":
            is_float = True
            capture.append(c)
            self._src.next()

            # at least 1 number
            if (c := self._src.curr()) not in _numbers:
                raise ast.ParseError(
                    self._src.name,
                    self._src.lineno,
                    start_charno,
                    "Invalid number literal. At least one number required in fractional part.",
                )
            capture.append(c)
            self._src.next()

            # as many numbers as you want
            while (c := self._src.curr()) in _numbers:
                capture.append(c)
                self._src.next()

        # optional exponent
        if (c := self._src.curr()) == "e":
            is_float = True
            capture.append(c)
            self._src.next()

            # optional starting '-'
            if (c := self._src.curr()) == "-":
                capture.append(c)
                self._src.next()

            # at least 1 number
            if (c := self._src.curr()) not in _numbers:
                raise ast.ParseError(
                    self._src.name,
                    self._src.lineno,
                    start_charno,
                    "Invalid number literal. At least one number required in fractional part.",
                )
            capture.append(c)
            self._src.next()

            # as many numbers as you want
            while (c := self._src.curr()) in _numbers:
                capture.append(c)
                self._src.next()

        value = literal_eval("".join(capture))
        if is_float:
            self._emit(ast.Float(self._src.name, self._src.lineno, start_charno, value))
        else:
            self._emit(
                ast.Integer(self._src.name, self._src.lineno, start_charno, value)
            )

    def _lex_string(self) -> None:
        start_charno = self._src.charno
        capture: list[str] = []
        self._src.next()
        while True:
            match self._src.curr():
                case '"':
                    self._src.next()
                    value = "".join(capture)
                    return self._emit(
                        ast.String(
                            self._src.name, self._src.lineno, start_charno, value
                        )
                    )
                case "\\":
                    escape_start_charno = self._src.charno
                    self._src.next()
                    match self._src.curr():
                        case c if c in 'nt\\"':
                            escape_value_translator = {
                                "n": "\n",
                                "t": "\t",
                                "\\": "\\",
                                '"': '"',
                            }
                            escape_value = escape_value_translator[c]
                            capture.append(escape_value)
                            self._src.next()
                        case "x":
                            self._src.next()
                            escape_capture: list[str] = []
                            for _ in range(2):
                                if (c := self._src.curr()) not in _hexchars:
                                    raise ast.ParseError(
                                        self._src.name,
                                        self._src.lineno,
                                        escape_start_charno,
                                        "Invalid escape sequence",
                                    )
                                escape_capture.append(c)
                                self._src.next()
                            escape_value = chr(int("".join(escape_capture), 16))
                            capture.append(escape_value)
                        case c:
                            raise ast.ParseError(
                                self._src.name,
                                self._src.lineno,
                                escape_start_charno,
                                "Invalid escape sequence",
                            )
                case c if c.isprintable():
                    capture.append(c)
                    self._src.next()
                case "\0" | "\n":
                    raise ast.ParseError(
                        self._src.name,
                        self._src.lineno,
                        start_charno,
                        "Unterminated string literal",
                    )
                case _:
                    raise ast.ParseError(
                        self._src.name,
                        self._src.lineno,
                        self._src.charno,
                        f"String contains non-printable character: '{c}'",
                    )

    def _lex_name(self) -> None:
        start_charno = self._src.charno
        capture: list[str] = []
        while (c := self._src.curr()) in _name_rest_chars:
            capture.append(c)
            self._src.next()
        value = "".join(capture)
        match value:
            case "null":
                self._emit(ast.Null(self._src.name, self._src.lineno, start_charno))
            case "true":
                self._emit(
                    ast.TrueToken(self._src.name, self._src.lineno, start_charno)
                )
            case "false":
                self._emit(
                    ast.FalseToken(self._src.name, self._src.lineno, start_charno)
                )
            case _:
                self._emit(
                    ast.Name(self._src.name, self._src.lineno, start_charno, value)
                )


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        file = sys.stdin
        name = "<stdin>"
    elif len(sys.argv) == 2:
        file = open(sys.argv[1])
        name = sys.argv[1]
    else:
        raise ValueError("Too many arguments")

    lexer = Lexer(_TextIOSourceIterator(name, file))

    while type(token := lexer.curr()) is not ast.EOF:
        print(token)
        lexer.next()
    print(token)
