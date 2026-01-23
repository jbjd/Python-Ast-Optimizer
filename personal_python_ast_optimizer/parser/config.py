from abc import abstractmethod
from collections.abc import Iterable, Iterator
from enum import Enum, EnumType
from types import EllipsisType

from personal_python_ast_optimizer.python_info import (
    default_functions_safe_to_exclude_in_test_expr,
)


class TypeHintsToSkip(Enum):
    NONE = 0
    # ALL might be unsafe, NamedTuple for example
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
        "classes_to_skip",
        "decorators_to_skip",
        "dict_keys_to_skip",
        "from_imports_to_skip",
        "functions_to_skip",
        "module_imports_to_skip",
        "variables_to_skip",
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
        "skip_asserts",
        "skip_dangling_expressions",
        "skip_overload_functions",
        "skip_type_hints",
    )

    def __init__(
        self,
        *,
        skip_dangling_expressions: bool = True,
        skip_type_hints: TypeHintsToSkip = TypeHintsToSkip.ALL_BUT_CLASS_VARS,
        skip_asserts: bool = False,
        skip_overload_functions: bool = False,
    ) -> None:
        self.skip_dangling_expressions: bool = skip_dangling_expressions
        self.skip_type_hints: TypeHintsToSkip = skip_type_hints
        self.skip_asserts: bool = skip_asserts
        self.skip_overload_functions: bool = skip_overload_functions


class OptimizationsConfig(_Config):
    __slots__ = (
        "assume_this_machine",
        "collection_concat_to_unpack",
        "enums_to_fold",
        "fold_constants",
        "functions_safe_to_exclude_in_test_expr",
        "remove_typing_cast",
        "remove_unused_imports",
        "simplify_named_tuples",
        "vars_to_fold",
    )

    def __init__(  # noqa: PLR0913
        self,
        *,
        vars_to_fold: dict[
            str, str | bytes | bool | int | float | complex | None | EllipsisType
        ]
        | None = None,
        enums_to_fold: Iterable[EnumType] | None = None,
        functions_safe_to_exclude_in_test_expr: set[str] | None = None,
        remove_unused_imports: bool = True,
        remove_typing_cast: bool = True,
        collection_concat_to_unpack: bool = False,
        fold_constants: bool = False,
        assume_this_machine: bool = False,
        simplify_named_tuples: bool = False,
    ) -> None:
        self.vars_to_fold: dict[
            str, str | bytes | bool | int | float | complex | None | EllipsisType
        ] = {} if vars_to_fold is None else vars_to_fold
        self.enums_to_fold: dict[str, dict[str, Enum]] = (
            {}
            if enums_to_fold is None
            else self._format_enums_to_fold_as_dict(enums_to_fold)
        )
        self.functions_safe_to_exclude_in_test_expr: set[str] = (
            functions_safe_to_exclude_in_test_expr
            or default_functions_safe_to_exclude_in_test_expr
        )
        self.remove_unused_imports: bool = remove_unused_imports
        self.remove_typing_cast: bool = remove_typing_cast
        self.collection_concat_to_unpack: bool = collection_concat_to_unpack
        self.assume_this_machine: bool = assume_this_machine
        self.fold_constants: bool = fold_constants
        self.simplify_named_tuples: bool = simplify_named_tuples

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
        "optimizations_config",
        "target_python_version",
        "token_types_config",
        "tokens_config",
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
