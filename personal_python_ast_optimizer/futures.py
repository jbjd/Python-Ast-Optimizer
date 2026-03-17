class Future:
    __slots__ = ("mandatory_version", "name")

    def __init__(self, name: str, mandatory_version: tuple[int, int]) -> None:
        self.name: str = name
        self.mandatory_version: tuple[int, int] = mandatory_version


future_to_mandatory_versions: list[Future] = [
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
    python version"""
    return [
        future.name
        for future in future_to_mandatory_versions
        if python_version >= future.mandatory_version
    ]
