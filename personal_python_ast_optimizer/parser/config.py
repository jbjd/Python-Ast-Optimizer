from collections.abc import Iterable, Iterator
from enum import Enum, EnumType, StrEnum
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


class _SkippableTokenTypes(StrEnum):
    CLASS = "class"
    DECORATOR = "decorator"
    DICT_KEYS = "dict keys"
    FROM_IMPORTS = "from imports"
    FUNCTION = "functions"
    MODULE_IMPORTS = "module imports"
    VARIABLES = "variables"


class TokensToSkip:
    __slots__ = ("_found", "_tokens_to_skip", "token_type")

    def __init__(
        self, tokens_to_skip: set[str] | None, token_type: _SkippableTokenTypes
    ) -> None:
        self._tokens_to_skip: set[str] = tokens_to_skip or set()
        self._found: set[str] = set()
        self.token_type: _SkippableTokenTypes = token_type

    def __bool__(self) -> bool:
        return bool(self._tokens_to_skip)

    def __contains__(self, key: str) -> bool:
        self._found.add(key)
        return self._tokens_to_skip.__contains__(key)

    def get_not_found_tokens(self) -> set[str]:
        return self._tokens_to_skip - self._found


class TokensConfig:
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
        classes_to_skip: set[str] | None = None,
        decorators_to_skip: set[str] | None = None,
        dict_keys_to_skip: set[str] | None = None,
        from_imports_to_skip: set[str] | None = None,
        functions_to_skip: set[str] | None = None,
        module_imports_to_skip: set[str] | None = None,
        variables_to_skip: set[str] | None = None,
        no_warn: set[str] | None = None,
    ) -> None:
        self.classes_to_skip = TokensToSkip(classes_to_skip, _SkippableTokenTypes.CLASS)
        self.decorators_to_skip = TokensToSkip(
            decorators_to_skip, _SkippableTokenTypes.DECORATOR
        )
        self.dict_keys_to_skip = TokensToSkip(
            dict_keys_to_skip, _SkippableTokenTypes.DICT_KEYS
        )
        self.from_imports_to_skip = TokensToSkip(
            from_imports_to_skip, _SkippableTokenTypes.FROM_IMPORTS
        )
        self.functions_to_skip = TokensToSkip(
            functions_to_skip, _SkippableTokenTypes.FUNCTION
        )
        self.module_imports_to_skip = TokensToSkip(
            module_imports_to_skip, _SkippableTokenTypes.MODULE_IMPORTS
        )
        self.variables_to_skip = TokensToSkip(
            variables_to_skip, _SkippableTokenTypes.VARIABLES
        )
        self._no_warn: set[str] = set() if no_warn is None else no_warn

    def get_missing_tokens_iter(self) -> Iterator[tuple[str, str]]:
        for attr in self.__slots__:
            if attr == "_no_warn":
                continue

            tokens_to_skip: TokensToSkip = getattr(self, attr)
            formatted_not_found_tokens: str = ",".join(
                t
                for t in tokens_to_skip.get_not_found_tokens()
                if t not in self._no_warn
            )
            if formatted_not_found_tokens != "":
                yield (tokens_to_skip.token_type, formatted_not_found_tokens)


class TokenTypesConfig:
    __slots__ = (
        "skip_asserts",
        "skip_dangling_expressions",
        "skip_generics",
        "skip_overload_functions",
        "skip_type_hints",
    )

    def __init__(
        self,
        *,
        skip_dangling_expressions: bool = True,
        skip_type_hints: TypeHintsToSkip = TypeHintsToSkip.ALL_BUT_CLASS_VARS,
        skip_generics: bool = False,
        skip_asserts: bool = False,
        skip_overload_functions: bool = False,
    ) -> None:
        if skip_generics and not skip_type_hints:
            raise ValueError("Can't skip Generics if not skipping type hints")

        self.skip_dangling_expressions: bool = skip_dangling_expressions
        self.skip_type_hints: TypeHintsToSkip = skip_type_hints
        self.skip_generics: bool = skip_generics and bool(skip_type_hints)
        self.skip_asserts: bool = skip_asserts
        self.skip_overload_functions: bool = skip_overload_functions


class OptimizationsConfig:
    __slots__ = (
        "assume_this_machine",
        "collection_concat_to_unpack",
        "enums_to_fold",
        "fold_constants",
        "fold_simple_function_locals",
        "functions_safe_to_exclude_in_test_expr",
        "remove_typing_cast",
        "remove_unused_imports",
        "remove_useless_else",
        "simplify_named_tuples",
        "unused_imports_to_preserve",
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
        unused_imports_to_preserve: Iterable[str] | None = None,
        remove_useless_else: bool = True,
        remove_typing_cast: bool = True,
        collection_concat_to_unpack: bool = False,
        fold_constants: bool = False,
        fold_simple_function_locals: bool = False,
        assume_this_machine: bool = False,
        simplify_named_tuples: bool = False,
    ) -> None:
        if unused_imports_to_preserve and not remove_unused_imports:
            raise ValueError("Can't preserve imports if remove_unused_imports is False")

        self.vars_to_fold: dict[
            str, str | bytes | bool | int | float | complex | None | EllipsisType
        ] = {} if vars_to_fold is None else vars_to_fold
        self.enums_to_fold: dict[str, dict[str, Enum]] = (
            {}
            if enums_to_fold is None
            else self._format_enums_to_fold_as_dict(enums_to_fold)
        )

        self.functions_safe_to_exclude_in_test_expr: set[str] = (
            default_functions_safe_to_exclude_in_test_expr
            if functions_safe_to_exclude_in_test_expr is None
            else functions_safe_to_exclude_in_test_expr
        )
        self.unused_imports_to_preserve: Iterable[str] = (
            unused_imports_to_preserve or []
        )

        self.remove_unused_imports: bool = remove_unused_imports
        self.remove_useless_else: bool = remove_useless_else
        self.remove_typing_cast: bool = remove_typing_cast
        self.collection_concat_to_unpack: bool = collection_concat_to_unpack
        self.assume_this_machine: bool = assume_this_machine
        self.fold_constants: bool = fold_constants
        self.fold_simple_function_locals: bool = fold_simple_function_locals
        self.simplify_named_tuples: bool = simplify_named_tuples

    @staticmethod
    def _format_enums_to_fold_as_dict(
        enums: Iterable[EnumType],
    ) -> dict[str, dict[str, Enum]]:
        """Given an Iterable of type Enum, turn them into a dict for quick lookup
        Where key is the Enum's class name and it points to a dict of strings
        mapping member name to value."""
        return {enum.__name__: enum._member_map_ for enum in enums}


class SkipConfig:
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
        tokens_config: TokensConfig | None = None,
        token_types_config: TokenTypesConfig | None = None,
        optimizations_config: OptimizationsConfig | None = None,
    ) -> None:
        self.module_name: str = module_name
        self.target_python_version: tuple[int, int] | None = target_python_version
        self.tokens_config: TokensConfig = tokens_config or TokensConfig()
        self.token_types_config: TokenTypesConfig = (
            token_types_config or TokenTypesConfig()
        )
        self.optimizations_config: OptimizationsConfig = (
            optimizations_config or OptimizationsConfig()
        )
