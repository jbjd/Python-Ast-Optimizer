class Futures:

    __slots__ = ("name", "mandatory_version")

    def __init__(self, name: str, mandatory_version: tuple[int, int]) -> None:
        self.name: str = name
        self.mandatory_version: tuple[int, int] = mandatory_version


futures_to_mandatory_version: list[Futures] = [
    Futures("nested_scopes", (2, 2)),
    Futures("generators", (2, 3)),
    Futures("with_statement", (2, 6)),
    Futures("division", (3, 0)),
    Futures("absolute_import", (3, 0)),
    Futures("print_function", (3, 0)),
    Futures("unicode_literals", (3, 0)),
    Futures("generator_stop", (3, 7)),
]


def get_unneeded_futures(python_version: tuple[int, int]) -> list[str]:
    """Returns list of __future__ imports that are unneeded in provided
    python version"""
    unneeded_futures: list[str] = [
        future.name
        for future in futures_to_mandatory_version
        if python_version >= future.mandatory_version
    ]

    return unneeded_futures
