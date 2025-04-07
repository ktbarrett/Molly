from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TextIO


class SourceIterator(ABC):
    """Iterates over characters of the source file."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the source object."""

    @property
    @abstractmethod
    def lineno(self) -> int:
        """The line number of the current character in the source object. Starts at 1."""

    @property
    @abstractmethod
    def charno(self) -> int:
        """The index into the line of the current character in the source object. Starts at 1."""

    @abstractmethod
    def curr(self) -> str:
        """The value of the current character in the source object."""

    @abstractmethod
    def next(self) -> None:
        """Moves to the next character in the source object."""


class TextIOSourceIterator(SourceIterator):
    def __init__(self, filename: str, io: TextIO) -> None:
        self._filename = filename
        self._io = io
        self._line: str = ""
        self._lineno = 0
        self._idx = 0

    @property
    def name(self) -> str:
        return self._filename

    @property
    def lineno(self) -> int:
        return self._lineno

    @property
    def charno(self) -> int:
        return self._idx + 1

    def curr(self) -> str:
        if not self._line:
            self._line = self._io.readline()
            if not self._line:
                return "\0"
            self._lineno += 1
            self._idx = 0
        return self._line[self._idx]

    def next(self) -> None:
        self._idx += 1
        if self._idx >= len(self._line):
            self._line = self._io.readline()
            self._lineno += 1
            self._idx = 0
