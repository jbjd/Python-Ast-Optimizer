"""Config files for running the AST optimizer."""

from collections.abc import Iterable
from enum import Enum
from typing import Literal

from personal_python_ast_optimizer.typing import FoldableConstant


class TypeHintsToSkip(Enum):
    NONE = 0
    # ALL might be unsafe, NamedTuple for example
    ALL = 1
    # Should be safe in most cases
    ALL_BUT_CLASS_VARS = 2

    def __bool__(self) -> bool:
        return self != TypeHintsToSkip.NONE


class TokensToSkip[T]:
    __slots__ = ("no_warn", "tokens")

    def __init__(
        self, tokens: Iterable[T], no_warn: Iterable[T] | Literal["*"] = "*"
    ) -> None:
        self.tokens: Iterable[T] = tokens
        self.no_warn: Iterable[T] | Literal["*"] = no_warn


class TokensToFold[T, V]:
    __slots__ = ("no_warn", "tokens")

    def __init__(
        self, tokens: dict[T, V], no_warn: Iterable[T] | Literal["*"] = "*"
    ) -> None:
        self.tokens: dict[T, V] = tokens
        self.no_warn: Iterable[T] | Literal["*"] = no_warn


class TokensToSkipConfig:
    __slots__ = (
        "assignments_to_skip",
        "classes_to_skip",
        "decorators_to_skip",
        "from_imports_to_skip",
        "functions_to_skip",
        "module_imports_to_skip",
    )

    def __init__(
        self,
        *,
        assignments_to_skip: TokensToSkip[str] | None = None,
        classes_to_skip: TokensToSkip[str] | None = None,
        decorators_to_skip: TokensToSkip[str] | None = None,
        from_imports_to_skip: TokensToSkip[tuple[str, str]] | None = None,
        functions_to_skip: TokensToSkip[str] | None = None,
        module_imports_to_skip: TokensToSkip[str] | None = None,
    ) -> None:
        self.assignments_to_skip: TokensToSkip[str] | None = assignments_to_skip
        self.classes_to_skip: TokensToSkip[str] | None = classes_to_skip
        self.decorators_to_skip: TokensToSkip[str] | None = decorators_to_skip
        self.from_imports_to_skip: TokensToSkip[tuple[str, str]] | None = (
            from_imports_to_skip
        )
        self.functions_to_skip: TokensToSkip[str] | None = functions_to_skip
        self.module_imports_to_skip: TokensToSkip[str] | None = module_imports_to_skip


class TokenTypesToSkipConfig:
    __slots__ = (
        "skip_asserts",
        "skip_dangling_expressions",
        "skip_generics_and_alias",
        "skip_type_hints",
    )

    def __init__(
        self,
        *,
        skip_dangling_expressions: bool = True,
        skip_type_hints: TypeHintsToSkip = TypeHintsToSkip.ALL_BUT_CLASS_VARS,
        skip_generics_and_alias: bool = False,
        skip_asserts: bool = False,
    ) -> None:
        if skip_generics_and_alias and skip_type_hints != TypeHintsToSkip.ALL:
            raise ValueError("Can't skip Generics unless all type hints are skipped")

        self.skip_dangling_expressions: bool = skip_dangling_expressions
        self.skip_type_hints: TypeHintsToSkip = skip_type_hints
        self.skip_generics_and_alias: bool = skip_generics_and_alias and bool(
            skip_type_hints
        )
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
        skip_typing_cast: bool = True,
        skip_useless_else: bool = True,
        skip_unused_imports: bool = True,
        unused_imports_to_preserve: Iterable[str] | None = None,
        skip_overload_functions: bool = False,
    ) -> None:
        if unused_imports_to_preserve and not skip_unused_imports:
            raise ValueError("Can't preserve imports if skip_unused_imports is False")

        self.skip_typing_cast: bool = skip_typing_cast
        self.skip_useless_else: bool = skip_useless_else
        self.skip_unused_imports: bool = skip_unused_imports
        self.unused_imports_to_preserve: Iterable[str] = (
            _NO_IMPORTS_TO_PRESERVE
            if unused_imports_to_preserve is None
            else unused_imports_to_preserve
        )
        self.skip_overload_functions: bool = skip_overload_functions


# Functions that have no side effects and thus are safe to remove
# if a test expression is found to be useless. For example:
# if "str(a) == 'a':pass" will be turned into just "str(a) == 'a'"
# but if its known str has no side effects then it can be fully removed
_default_functions_safe_to_exclude_in_test_expr: set[str] = {
    "int",
    "str",
    "isinstance",
    "getattr",
    "hasattr",
}


class PerfOptimizationsConfig:
    __slots__ = (
        "collection_concat_to_unpack",
        "fold_constants",
        "fold_simple_function_locals",
        "functions_safe_to_exclude_in_test_expr",
        "names_to_fold",
        "simplify_named_tuple",
    )

    def __init__(
        self,
        *,
        fold_constants: bool = False,
        fold_simple_function_locals: bool = False,
        names_to_fold: TokensToFold[str, FoldableConstant] | None = None,
        functions_safe_to_exclude_in_test_expr: set[str] | None = None,
        collection_concat_to_unpack: bool = False,
        simplify_named_tuple: bool = False,
    ) -> None:
        self.fold_constants: bool = fold_constants
        self.fold_simple_function_locals: bool = fold_simple_function_locals

        self.names_to_fold: TokensToFold[str, FoldableConstant] | None = names_to_fold

        self.functions_safe_to_exclude_in_test_expr: set[str] = (
            _default_functions_safe_to_exclude_in_test_expr
            if functions_safe_to_exclude_in_test_expr is None
            else functions_safe_to_exclude_in_test_expr
        )

        self.collection_concat_to_unpack: bool = collection_concat_to_unpack
        self.simplify_named_tuple: bool = simplify_named_tuple


class OptimizeConfig:
    __slots__ = (
        "code_to_skip",
        "perf_optimizations",
        "token_types_to_skip",
        "tokens_to_skip",
    )

    def __init__(
        self,
        *,
        code_to_skip: CodeToSkipConfig | None = None,
        tokens_to_skip: TokensToSkipConfig | None = None,
        token_types_to_skip: TokenTypesToSkipConfig | None = None,
        perf_optimizations: PerfOptimizationsConfig | None = None,
    ) -> None:
        self.code_to_skip: CodeToSkipConfig = (
            CodeToSkipConfig() if code_to_skip is None else code_to_skip
        )
        self.tokens_to_skip: TokensToSkipConfig = (
            TokensToSkipConfig() if tokens_to_skip is None else tokens_to_skip
        )
        self.token_types_to_skip: TokenTypesToSkipConfig = (
            TokenTypesToSkipConfig()
            if token_types_to_skip is None
            else token_types_to_skip
        )
        self.perf_optimizations: PerfOptimizationsConfig = (
            PerfOptimizationsConfig()
            if perf_optimizations is None
            else perf_optimizations
        )
