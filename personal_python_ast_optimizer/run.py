"""Convienience functions for running the ast optimizer."""

import ast

from personal_python_ast_optimizer._optimize.transformers import (
    FirstPassOptimizer,
    UnusedImportSkipper,
)
from personal_python_ast_optimizer.config import (
    CodeToSkipConfig,
    OptimizeConfig,
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
    code_to_skip_config: CodeToSkipConfig = skip_config.code_to_skip_config
    token_types_config: TokenTypesToSkipConfig = skip_config.token_types_config
    FirstPassOptimizer(
        token_types_config.skip_dangling_expressions,
        token_types_config.skip_type_hints,
        token_types_config.skip_generics,
        token_types_config.skip_asserts,
        code_to_skip_config.skip_typing_cast,
        code_to_skip_config.skip_overload_functions,
    ).visit_if_has_work(module)

    UnusedImportSkipper(
        code_to_skip_config.skip_unused_imports,
        code_to_skip_config.unused_imports_to_preserve,
    ).visit_if_has_work(module)


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
