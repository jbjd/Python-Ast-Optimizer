import re
import warnings
from collections.abc import Iterable

from personal_python_ast_optimizer.regex.classes import RegexReplacement


def apply_regex(
    source: str,
    regex_replacement: RegexReplacement | Iterable[RegexReplacement],
    warning_id: str = "",
) -> str:
    """Runs a series of regex on given source.
    Passing warning_id enabled warnings when patterns are not found"""
    if isinstance(regex_replacement, RegexReplacement):
        regex_replacement = (regex_replacement,)

    for regex, replacement, flags, count in regex_replacement:
        source, count_replaced = re.subn(
            regex, replacement, source, flags=flags, count=count
        )
        if count_replaced == 0 and warning_id != "":
            warnings.warn(f"{warning_id}: Unused regex {regex}")

    return source


def apply_regex_to_file(
    path: str,
    regex_replacement: RegexReplacement | Iterable[RegexReplacement],
    warning_id: str = "",
    encoding: str = "utf-8",
):
    """Wraps apply_regex with opening and writing to a file"""
    with open(path, encoding=encoding) as fp:
        source: str = fp.read()

    source = apply_regex(source, regex_replacement, warning_id)

    with open(path, "w", encoding=encoding) as fp:
        fp.write(source)
