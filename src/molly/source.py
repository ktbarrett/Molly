from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TextIO


class SourceIterator(ABC):
    @property
    @abstractmethod
    def filename(self) -> str: ...

    @property
    @abstractmethod
    def lineno(self) -> int: ...

    @property
    @abstractmethod
    def charno(self) -> int: ...

    @abstractmethod
    def peek(self) -> str: ...

    @abstractmethod
    def next(self) -> str: ...


class TextIOSourceIterator(SourceIterator):
    def __init__(self, filename: str, io: TextIO) -> None:
        self._filename = filename
        self._io = io
        self._line: str = ""
        self._lineno = 0
        self._idx = 0

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def lineno(self) -> int:
        return self._lineno

    @property
    def charno(self) -> int:
        return self._idx + 1

    def peek(self) -> str:
        if self._idx >= len(self._line):
            self._line = self._io.readline()
            if not self._line:
                return "\x00"
            self._lineno += 1
            self._idx = 0
        return self._line[self._idx]

    def next(self) -> str:
        res = self.peek()
        self._idx += 1
        return res
