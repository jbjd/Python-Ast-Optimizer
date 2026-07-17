"""Entrypoint for running the AST optimizer."""

import ast

from personal_python_ast_optimizer._optimize.transformers import (
    FirstPassOptimizer,
    LastPassOptimizer,
    OptimizationPass,
)
from personal_python_ast_optimizer._optimize.utils import TokensTracker
from personal_python_ast_optimizer.config import (
    CodeToSkipConfig,
    OptimizeConfig,
    PerfOptimizationsConfig,
    TokensToSkipConfig,
    TokenTypesToSkipConfig,
)
from personal_python_ast_optimizer.minifier import MinifyUnparser
from personal_python_ast_optimizer.typing import Unparser


def optimize_module(
    module: ast.Module,
    optimize_config: OptimizeConfig,
    file_name: str = "",
) -> None:
    """Optimizes a Python AST by removing unneeded node, replacements of slower
    code, etc.

    :param module: Module to optimize
    :param optimize_config: Config for what is allowed to be optimized
    :param file_name: Optionally used for logging"""
    code_to_skip: CodeToSkipConfig = optimize_config.code_to_skip
    tokens_to_skip: TokensToSkipConfig = optimize_config.tokens_to_skip
    token_types_to_skip: TokenTypesToSkipConfig = optimize_config.token_types_to_skip
    perf_optimizations: PerfOptimizationsConfig = optimize_config.perf_optimizations

    tokens_to_skip_tracker = TokensTracker(
        tokens_to_skip.assignments_to_skip,
        tokens_to_skip.classes_to_skip,
        tokens_to_skip.decorators_to_skip,
        tokens_to_skip.from_imports_to_skip,
        tokens_to_skip.functions_to_skip,
        tokens_to_skip.module_imports_to_skip,
        perf_optimizations.calls_to_fold,
        perf_optimizations.names_to_fold,
    )

    first_pass = FirstPassOptimizer(
        tokens_to_skip_tracker,
        perf_optimizations.fold_constants,
        perf_optimizations.fold_simple_function_locals,
        perf_optimizations.functions_safe_to_exclude_in_test_expr,
        perf_optimizations.collection_concat_to_unpack,
        perf_optimizations.simplify_named_tuple,
        token_types_to_skip.skip_dangling_expressions,
        token_types_to_skip.skip_type_hints,
        token_types_to_skip.skip_generics_and_alias,
        token_types_to_skip.skip_asserts,
        code_to_skip.skip_typing_cast,
        code_to_skip.skip_overload_functions,
        code_to_skip.skip_useless_else,
    )
    first_pass.visit(module)

    tokens_to_skip_tracker.warn_not_found_skips(file_name)

    additional_pass_needed: bool = first_pass.additional_pass_needed
    if additional_pass_needed:
        optimization_pass = OptimizationPass(
            perf_optimizations.fold_constants,
            perf_optimizations.fold_simple_function_locals,
            perf_optimizations.functions_safe_to_exclude_in_test_expr,
        )
        while additional_pass_needed:
            optimization_pass.visit(module)
            additional_pass_needed = optimization_pass.additional_pass_needed

    LastPassOptimizer(
        code_to_skip.skip_unused_imports,
        code_to_skip.unused_imports_to_preserve,
    ).visit(module)


def optimize_source(
    source: str,
    optimize_config: OptimizeConfig,
    unparser: Unparser,
    file_name: str = "",
) -> str:
    """Optimizes Python code by removing unneeded node, replacements of slower
    code, etc.

    :param module: Module to optimize
    :param optimize_config: Config for what is allowed to be optimized
    :param unparser: A class that can convert the ast.Module back into python
    :param file_name: Optionally used for `ast.parse` and logging
    :returns: Optimized python code"""
    module: ast.Module = ast.parse(source, file_name)
    optimize_module(module, optimize_config)
    return unparser.visit(module)


def optimize_source_and_minify(
    source: str, optimize_config: OptimizeConfig, file_name: str = ""
) -> str:
    """Optimizes Python code by removing unneeded node, replacements of slower
    code, etc. and returns it in a minified format.

    :param module: Module to optimize
    :param optimize_config: Config for what is allowed to be optimized
    :param file_name: Optionally used for `ast.parse` and logging
    :returns: Optimized python code"""
    return optimize_source(source, optimize_config, MinifyUnparser(), file_name)
