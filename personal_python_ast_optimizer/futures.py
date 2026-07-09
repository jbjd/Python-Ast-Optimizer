"""Details information about __future__ imports in Python."""

FUTURE_IMPORT_NAME: str = "__future__"


class Future:
    """Represents a __future__ import with its name and mandatory version."""

    __slots__ = ("mandatory_version", "name")

    def __init__(self, name: str, mandatory_version: tuple[int, int]) -> None:
        self.name: str = name
        self.mandatory_version: tuple[int, int] = mandatory_version


mandatory_futures: list[Future] = [
    Future("nested_scopes", (2, 2)),
    Future("generators", (2, 3)),
    Future("with_statement", (2, 6)),
    Future("division", (3, 0)),
    Future("absolute_import", (3, 0)),
    Future("print_function", (3, 0)),
    Future("unicode_literals", (3, 0)),
    Future("generator_stop", (3, 7)),
]


def get_unneeded_futures(python_version: tuple[int, int]) -> list[str]:
    """Returns __future__ imports that are unneeded in provided
    python version.

    :param python_version: Version to compare against
    :returns: List of __future__ imports that can be removed"""
    return [
        future.name
        for future in mandatory_futures
        if python_version >= future.mandatory_version
    ]
