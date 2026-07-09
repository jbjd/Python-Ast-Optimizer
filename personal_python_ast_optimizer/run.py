"""Convienience functions for running the ast optimizer."""

import ast

from personal_python_ast_optimizer._optimize.transformers import (
    FirstPassOptimizer,
    LastPassOptimizer,
    OptimizationPass,
)
from personal_python_ast_optimizer._optimize.utils import UserTokensToSkipTracker
from personal_python_ast_optimizer.config import (
    CodeToFoldConfig,
    CodeToSkipConfig,
    OptimizeConfig,
    OtherOptimizationsConfig,
    TokensToSkipConfig,
    TokenTypesToSkipConfig,
)
from personal_python_ast_optimizer.minifier import MinifyUnparser
from personal_python_ast_optimizer.typing import Unparser


def optimize_module(
    module: ast.Module,
    skip_config: OptimizeConfig,
    file_name: str = "<unknown>",  # noqa: ARG001
) -> None:
    """Optimizes a Python AST by removing unneeded node, replacements of slower
    code, etc.

    :param module: Module to optimize
    :param skip_config: Config for what is allowed to be optimized
    :param file_name: Optionally used for logging"""
    code_to_fold: CodeToFoldConfig = skip_config.code_to_fold
    code_to_skip: CodeToSkipConfig = skip_config.code_to_skip
    tokens_to_skip: TokensToSkipConfig = skip_config.tokens_to_skip
    token_types_to_skip: TokenTypesToSkipConfig = skip_config.token_types_to_skip
    other_optimizations: OtherOptimizationsConfig = skip_config.other_optimizations

    FirstPassOptimizer(
        UserTokensToSkipTracker(
            tokens_to_skip.assignments_to_skip,
            tokens_to_skip.classes_to_skip,
            tokens_to_skip.decorators_to_skip,
            tokens_to_skip.dict_keys_to_skip,
            tokens_to_skip.from_imports_to_skip,
            tokens_to_skip.functions_to_skip,
            tokens_to_skip.module_imports_to_skip,
            tokens_to_skip.no_warn,
        ),
        code_to_fold.fold_constants,
        token_types_to_skip.skip_dangling_expressions,
        token_types_to_skip.skip_type_hints,
        token_types_to_skip.skip_generics,
        token_types_to_skip.skip_asserts,
        code_to_skip.skip_typing_cast,
        code_to_skip.skip_overload_functions,
        other_optimizations.target_python_version,
    ).visit(module)

    optimization_passes = OptimizationPass(code_to_fold.fold_constants)
    while optimization_passes.has_work():
        optimization_passes.visit_Module(module)

    LastPassOptimizer(
        code_to_skip.skip_unused_imports,
        code_to_skip.unused_imports_to_preserve,
    ).visit(module)


def optimize_source(
    source: str,
    skip_config: OptimizeConfig,
    unparser: Unparser,
    file_name: str = "<unknown>",
) -> str:
    """Optimizes Python code by removing unneeded node, replacements of slower
    code, etc.

    :param module: Module to optimize
    :param skip_config: Config for what is allowed to be optimized
    :param unparser: A class that can convert the ast.Module back into python
    :param file_name: Optionally used for `ast.parse` and logging
    :returns: Optimized python code"""
    module: ast.Module = ast.parse(source, file_name)
    optimize_module(module, skip_config)
    return unparser.visit(module)


def optimize_source_and_minify(
    source: str, skip_config: OptimizeConfig, file_name: str = "<unknown>"
) -> str:
    """Optimizes Python code by removing unneeded node, replacements of slower
    code, etc. and returns it in a minified format.

    :param module: Module to optimize
    :param skip_config: Config for what is allowed to be optimized
    :param file_name: Optionally used for `ast.parse` and logging
    :returns: Optimized python code"""
    return optimize_source(source, skip_config, MinifyUnparser(), file_name)
