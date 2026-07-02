from collections.abc import Iterable, Iterator
from enum import Enum, EnumType, StrEnum
from types import EllipsisType


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

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False

        contains: bool = self._tokens_to_skip.__contains__(key)
        if contains:
            self._found.add(key)

        return contains

    def get_not_found_tokens(self) -> set[str]:
        return self._tokens_to_skip - self._found


class UserTokensToSkipConfig:
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

    def __init__(
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


class TokenTypesToSkipConfig:
    __slots__ = (
        "skip_asserts",
        "skip_dangling_expressions",
        "skip_generics",
        "skip_type_hints",
    )

    def __init__(
        self,
        *,
        skip_dangling_expressions: bool = True,
        skip_type_hints: TypeHintsToSkip = TypeHintsToSkip.ALL_BUT_CLASS_VARS,
        skip_generics: bool = False,
        skip_asserts: bool = False,
    ) -> None:
        if skip_generics and not skip_type_hints:
            raise ValueError("Can't skip Generics if not skipping type hints")

        self.skip_dangling_expressions: bool = skip_dangling_expressions
        self.skip_type_hints: TypeHintsToSkip = skip_type_hints
        self.skip_generics: bool = skip_generics and bool(skip_type_hints)
        self.skip_asserts: bool = skip_asserts


_NO_IMPORTS_TO_PRESERVE: list[str] = []


class CodeToSkipConfig:
    __slots__ = (
        "skip_overload_functions",
        "skip_typing_cast",
        "skip_unused_imports",
        "skip_useless_else",
        "unused_imports_to_preserve",
    )

    def __init__(
        self,
        *,
        skip_overload_functions: bool = False,
        skip_typing_cast: bool = True,
        skip_useless_else: bool = True,
        skip_unused_imports: bool = True,
        unused_imports_to_preserve: Iterable[str] | None = None,
    ) -> None:
        if unused_imports_to_preserve and not skip_unused_imports:
            raise ValueError("Can't preserve imports if skip_unused_imports is False")

        self.skip_overload_functions: bool = skip_overload_functions
        self.skip_typing_cast: bool = skip_typing_cast
        self.skip_useless_else: bool = skip_useless_else
        self.skip_unused_imports: bool = skip_unused_imports
        self.unused_imports_to_preserve: Iterable[str] = (
            _NO_IMPORTS_TO_PRESERVE
            if unused_imports_to_preserve is None
            else unused_imports_to_preserve
        )


type FoldableConstant = str | bytes | bool | int | float | complex | None | EllipsisType


class CodeToFoldConfig:
    __slots__ = (
        "enums_to_fold",
        "fold_constants",
        "fold_simple_function_locals",
        "vars_to_fold",
    )

    def __init__(
        self,
        *,
        enums_to_fold: Iterable[EnumType] | None = None,
        fold_constants: bool = False,
        fold_simple_function_locals: bool = False,
        vars_to_fold: dict[str, FoldableConstant] | None = None,
    ) -> None:
        self.enums_to_fold: dict[str, dict[str, Enum]] = (
            {}
            if enums_to_fold is None
            else self._format_enums_to_fold_as_dict(enums_to_fold)
        )

        self.fold_constants: bool = fold_constants
        self.fold_simple_function_locals: bool = fold_simple_function_locals

        self.vars_to_fold: dict[str, FoldableConstant] = (
            {} if vars_to_fold is None else vars_to_fold
        )

    @staticmethod
    def _format_enums_to_fold_as_dict(
        enums: Iterable[EnumType],
    ) -> dict[str, dict[str, Enum]]:
        return {enum.__name__: enum._member_map_ for enum in enums}


# Functions that have no side effects and thus are safe to remove
# if a test expression is found to be useless. For example:
# if "str(a) == 'a':pass" will be turned into just "str(a) == 'a'"
# but if its known str has no side effects then it can be fully removed
default_functions_safe_to_exclude_in_test_expr: set[str] = {
    "int",
    "str",
    "isinstance",
    "getattr",
    "hasattr",
}


class ExtraOptimizationsConfig:
    __slots__ = (
        "assume_this_machine",
        "collection_concat_to_unpack",
        "functions_safe_to_exclude_in_test_expr",
        "simplify_named_tuples",
        "target_python_version",
    )

    MIN_TARGET_PYTHON: tuple[int, int] = (3, 0)

    def __init__(
        self,
        *,
        assume_this_machine: bool = False,
        collection_concat_to_unpack: bool = False,
        functions_safe_to_exclude_in_test_expr: set[str] | None = None,
        simplify_named_tuples: bool = False,
        target_python_version: tuple[int, int] = MIN_TARGET_PYTHON,
    ) -> None:
        if target_python_version < self.MIN_TARGET_PYTHON:
            raise ValueError("Target Python version must be at least 3.0")

        self.assume_this_machine: bool = assume_this_machine
        self.collection_concat_to_unpack: bool = collection_concat_to_unpack

        self.functions_safe_to_exclude_in_test_expr: set[str] = (
            default_functions_safe_to_exclude_in_test_expr
            if functions_safe_to_exclude_in_test_expr is None
            else functions_safe_to_exclude_in_test_expr
        )

        self.simplify_named_tuples: bool = simplify_named_tuples
        self.target_python_version: tuple[int, int] = target_python_version


class OptimizeConfig:
    __slots__ = (
        "code_to_fold_config",
        "code_to_skip_config",
        "optimizations_config",
        "token_types_config",
        "tokens_config",
    )

    def __init__(
        self,
        *,
        code_to_fold_config: CodeToFoldConfig | None = None,
        code_to_skip_config: CodeToSkipConfig | None = None,
        tokens_config: UserTokensToSkipConfig | None = None,
        token_types_config: TokenTypesToSkipConfig | None = None,
        optimizations_config: ExtraOptimizationsConfig | None = None,
    ) -> None:

        self.code_to_fold_config: CodeToFoldConfig = (
            CodeToFoldConfig() if code_to_fold_config is None else code_to_fold_config
        )
        self.code_to_skip_config: CodeToSkipConfig = (
            CodeToSkipConfig() if code_to_skip_config is None else code_to_skip_config
        )
        self.tokens_config: UserTokensToSkipConfig = (
            UserTokensToSkipConfig() if tokens_config is None else tokens_config
        )
        self.token_types_config: TokenTypesToSkipConfig = (
            TokenTypesToSkipConfig()
            if token_types_config is None
            else token_types_config
        )
        self.optimizations_config: ExtraOptimizationsConfig = (
            ExtraOptimizationsConfig()
            if optimizations_config is None
            else optimizations_config
        )
