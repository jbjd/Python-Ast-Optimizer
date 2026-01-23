import re
from collections.abc import Iterable, Iterator


class RegexReplacement:
    """Represents arguments to a regex replacement call like re.sub"""

    __slots__ = ("count", "flags", "pattern", "replacement")

    def __init__(
        self, pattern: str, replacement: str = "", flags: int = 0, count: int = 1
    ) -> None:
        self.pattern: str = pattern
        self.replacement: str = replacement
        self.flags: int = flags
        self.count: int = count

    def __iter__(self) -> Iterator:
        yield self.pattern
        yield self.replacement
        yield self.flags
        yield self.count


class RegexNoMatchException(Exception):
    pass


def re_replace(
    source: str,
    regex_replacement: RegexReplacement | Iterable[RegexReplacement],
    raise_if_not_applied: bool = False,
) -> str:
    """Runs a series of regex on given source.
    Passing warning_id enabled warnings when patterns are not found"""
    if isinstance(regex_replacement, RegexReplacement):
        regex_replacement = (regex_replacement,)

    unused_regex: list[str] = []

    for regex, replacement, flags, count in regex_replacement:
        source, count_replaced = re.subn(
            regex, replacement, source, flags=flags, count=count
        )
        if count_replaced == 0 and raise_if_not_applied:
            unused_regex.append(regex)

    if unused_regex:
        raise RegexNoMatchException(
            f"Found {len(unused_regex)} unused regex: {unused_regex}"
        )

    return source


def re_replace_file(
    path: str,
    regex_replacement: RegexReplacement | Iterable[RegexReplacement],
    encoding: str = "utf-8",
    raise_if_not_applied: bool = False,
):
    """Wraps apply_regex with opening and writing to a file"""
    with open(path, encoding=encoding) as fp:
        source: str = fp.read()

    source = re_replace(source, regex_replacement, raise_if_not_applied)

    with open(path, "w", encoding=encoding) as fp:
        fp.write(source)
