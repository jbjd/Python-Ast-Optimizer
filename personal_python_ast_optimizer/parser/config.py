from abc import abstractmethod
from collections.abc import Iterable, Iterator
from enum import Enum, EnumType
from types import EllipsisType


class TypeHintsToSkip(Enum):
    NONE = 0
    # ALL might be unsafe, NamedTuple or TypedDict for example
    ALL = 1
    # Should be safe in most cases
    ALL_BUT_CLASS_VARS = 2

    def __bool__(self) -> bool:
        return self != TypeHintsToSkip.NONE


class TokensToSkip(dict[str, int]):
    __slots__ = ("token_type",)

    def __init__(self, tokens_to_skip: Iterable[str] | None, token_type: str) -> None:
        tokens_and_counts: dict[str, int] = dict.fromkeys(tokens_to_skip or [], 0)
        super().__init__(tokens_and_counts)

        self.token_type: str = token_type

    def __contains__(self, key: str) -> bool:  # type: ignore
        """Returns if token is marked to skip and
        increments internal counter when True is returned"""
        contains: bool = super().__contains__(key)

        if contains:
            self[key] += 1

        return contains

    def get_not_found_tokens(self) -> set[str]:
        return {token for token, found_count in self.items() if found_count == 0}


class _Config:
    __slots__ = ()

    @abstractmethod
    def __init__(self) -> None:
        pass

    def has_code_to_skip(self) -> bool:
        return any(getattr(self, attr) for attr in self.__slots__)  # type: ignore


class TokensConfig(_Config):
    __slots__ = (
        "_no_warn",
        "from_imports_to_skip",
        "functions_to_skip",
        "variables_to_skip",
        "classes_to_skip",
        "dict_keys_to_skip",
        "decorators_to_skip",
        "module_imports_to_skip",
    )

    def __init__(  # noqa: PLR0913
        self,
        *,
        from_imports_to_skip: set[str] | None = None,
        functions_to_skip: set[str] | None = None,
        variables_to_skip: set[str] | None = None,
        classes_to_skip: set[str] | None = None,
        dict_keys_to_skip: set[str] | None = None,
        decorators_to_skip: set[str] | None = None,
        module_imports_to_skip: set[str] | None = None,
        no_warn: set[str] | None = None,
    ):
        self.from_imports_to_skip = TokensToSkip(from_imports_to_skip, "from imports")
        self.functions_to_skip = TokensToSkip(functions_to_skip, "functions")
        self.variables_to_skip = TokensToSkip(variables_to_skip, "variables")
        self.classes_to_skip = TokensToSkip(classes_to_skip, "classes")
        self.dict_keys_to_skip = TokensToSkip(dict_keys_to_skip, "dict keys")
        self.decorators_to_skip = TokensToSkip(decorators_to_skip, "decorators")
        self.module_imports_to_skip = TokensToSkip(
            module_imports_to_skip, "module imports"
        )
        self._no_warn: set[str] = no_warn if no_warn is not None else set()

    def __iter__(self) -> Iterator[TokensToSkip]:
        for attr in self.__slots__:
            if attr != "_no_warn":
                yield getattr(self, attr)

    def has_code_to_skip(self) -> bool:
        return any(self)  # type: ignore

    def get_missing_tokens_iter(self) -> Iterator[tuple[str, str]]:
        for tokens_to_skip in self:
            not_found_tokens: list[str] = [
                t
                for t in tokens_to_skip.get_not_found_tokens()
                if t not in self._no_warn
            ]
            if not_found_tokens:
                yield (tokens_to_skip.token_type, ",".join(not_found_tokens))


class TokenTypesConfig(_Config):
    __slots__ = (
        "simplify_named_tuples",
        "skip_dangling_expressions",
        "skip_type_hints",
        "skip_overload_functions",
    )

    def __init__(
        self,
        *,
        skip_dangling_expressions: bool = True,
        skip_type_hints: TypeHintsToSkip = TypeHintsToSkip.ALL_BUT_CLASS_VARS,
        skip_overload_functions: bool = False,
        simplify_named_tuples: bool = False,
    ) -> None:
        self.skip_dangling_expressions: bool = skip_dangling_expressions
        self.skip_type_hints: TypeHintsToSkip = skip_type_hints
        self.skip_overload_functions: bool = skip_overload_functions
        self.simplify_named_tuples: bool = simplify_named_tuples


class OptimizationsConfig(_Config):
    __slots__ = (
        "vars_to_fold",
        "enums_to_fold",
        "remove_unused_imports",
        "fold_constants",
        "assume_this_machine",
    )

    def __init__(
        self,
        vars_to_fold: dict[
            str, str | bytes | bool | int | float | complex | None | EllipsisType
        ]
        | None = None,
        enums_to_fold: Iterable[EnumType] | None = None,
        fold_constants: bool = True,
        remove_unused_imports: bool = True,
        assume_this_machine: bool = False,
    ) -> None:
        self.vars_to_fold: dict[
            str, str | bytes | bool | int | float | complex | None | EllipsisType
        ] = {} if vars_to_fold is None else vars_to_fold
        self.enums_to_fold: dict[str, dict[str, Enum]] = (
            {}
            if enums_to_fold is None
            else self._format_enums_to_fold_as_dict(enums_to_fold)
        )
        self.remove_unused_imports: bool = remove_unused_imports
        self.assume_this_machine: bool = assume_this_machine
        self.fold_constants: bool = fold_constants

    @staticmethod
    def _format_enums_to_fold_as_dict(
        enums: Iterable[EnumType],
    ) -> dict[str, dict[str, Enum]]:
        """Given an Iterable of type Enum, turn them into a dict for quick lookup
        Where key is the Enum's class name and it points to a dict of strings
        mapping member name to value."""
        return {enum.__name__: enum._member_map_ for enum in enums}


class SkipConfig(_Config):
    __slots__ = (
        "module_name",
        "target_python_version",
        "token_types_config",
        "tokens_config",
        "optimizations_config",
    )

    def __init__(
        self,
        module_name: str,
        *,
        target_python_version: tuple[int, int] | None = None,
        tokens_config: TokensConfig = TokensConfig(),
        token_types_config: TokenTypesConfig = TokenTypesConfig(),
        optimizations_config: OptimizationsConfig = OptimizationsConfig(),
    ) -> None:
        self.module_name: str = module_name
        self.target_python_version: tuple[int, int] | None = target_python_version
        self.tokens_config: TokensConfig = tokens_config
        self.token_types_config: TokenTypesConfig = token_types_config
        self.optimizations_config: OptimizationsConfig = optimizations_config

    def has_code_to_skip(self) -> bool:
        return (
            self.target_python_version is not None
            or self.tokens_config.has_code_to_skip()
            or self.token_types_config.has_code_to_skip()
            or self.optimizations_config.has_code_to_skip()
        )
