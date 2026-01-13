from collections.abc import Iterator


class RegexReplacement:
    """Represents arguments to a regex replacement call like re.sub"""

    __slots__ = ("pattern", "replacement", "flags", "count")

    def __init__(
        self, pattern: str, replacement: str = "", flags: int = 0, count: int = 0
    ) -> None:
        self.pattern: str = pattern
        self.replacement: str = replacement
        self.flags: int = flags
        self.count: int = count

    def __iter__(self) -> Iterator:
        for attr in self.__slots__:
            yield getattr(self, attr)
