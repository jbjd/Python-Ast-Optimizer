import ast
import os
from collections.abc import Callable, Iterable
from enum import Enum
from typing import Self

from personal_python_ast_optimizer.config import (
    CodeToSkipConfig,
    OptimizeConfig,
    PerfOptimizationsConfig,
    TokensToSkipConfig,
    TokenTypesToSkipConfig,
)
from personal_python_ast_optimizer.parser._base import (
    AstNodeTransformerBase,
    AstNodeVisitorBase,
)
from personal_python_ast_optimizer.parser.utils import get_node_name, skip_decorators

machine_dependent_functions: dict[str, int | None] = {"os.cpu_count": os.cpu_count()}


class _NodeContext(Enum):
    NONE = 0
    CLASS = 1
    FUNCTION = 2


class _OpFolder(AstNodeTransformerBase):
    __slots__ = ("perf_optimizations",)

    def __init__(
        self,
        perf_optimizations: PerfOptimizationsConfig,
    ) -> None:
        super().__init__()
        self.perf_optimizations: PerfOptimizationsConfig = perf_optimizations


class AstNodeSkipper(_OpFolder):
    __slots__ = (
        "_has_imports",
        "_node_context",
        "code_to_skip",
        "module_name",
        "target_python_version",
        "token_types_to_skip",
        "tokens_to_skip",
    )

    def __init__(self, module_name: str, config: OptimizeConfig) -> None:
        super().__init__(config.perf_optimizations, config.perf_optimizations)

        self.module_name: str = module_name
        self.target_python_version: tuple[int, int] | None = (
            config.perf_optimizations.target_python_version
        )
        self.code_to_skip: CodeToSkipConfig = config.code_to_skip
        self.token_types_to_skip: TokenTypesToSkipConfig = config.token_types_to_skip
        self.tokens_to_skip: TokensToSkipConfig = config.tokens_to_skip

        self._has_imports: bool = False
        self._node_context: _NodeContext = _NodeContext.NONE

    @staticmethod
    def _within_class_node[*Ts, R](
        function: Callable[["AstNodeSkipper", *Ts], R],
    ) -> Callable[["AstNodeSkipper", *Ts], R]:
        def wrapper(self: Self, *args: *Ts) -> R:
            previous_value: _NodeContext = self._node_context
            self._node_context = _NodeContext.CLASS
            try:
                return function(self, *args)
            finally:
                self._node_context = previous_value

        return wrapper

    @staticmethod
    def _within_function_node[*Ts, R](
        function: Callable[["AstNodeSkipper", *Ts], R],
    ) -> Callable[["AstNodeSkipper", *Ts], R]:
        def wrapper(self: Self, *args: *Ts) -> R:
            # In case we have a function in a function
            previous_value: _NodeContext = self._node_context
            self._node_context = _NodeContext.FUNCTION
            try:
                return function(self, *args)
            finally:
                self._node_context = previous_value

        return wrapper

    def generic_visit(self, node: ast.AST) -> ast.AST:  # noqa: C901
        """Modified version of super class's generic_visit
        to extend functionality"""
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                new_values: list = []
                for i in range(len(old_value)):
                    value = old_value[i]
                    if isinstance(value, ast.AST):
                        value = self.visit(value)

                        if new_values:
                            previous_value = new_values[-1]
                            if (
                                isinstance(value, ast.Import)
                                and isinstance(previous_value, ast.Import)
                            ) or (
                                isinstance(value, ast.ImportFrom)
                                and isinstance(previous_value, ast.ImportFrom)
                                and value.module == previous_value.module
                                and value.level == previous_value.level
                            ):
                                previous_value.names += value.names
                                continue

                        if value is None or (
                            self.token_types_to_skip.skip_dangling_expressions
                            and isinstance(value, ast.Expr)
                            and isinstance(value.value, ast.Constant)
                        ):
                            continue

                        if not isinstance(value, ast.AST):
                            new_values.extend(value)
                            continue

                    new_values.append(value)

                if (
                    not isinstance(node, ast.Module)
                    and not new_values
                    and field == "body"
                ):
                    new_values.append(ast.Pass())

                old_value[:] = new_values

            elif isinstance(old_value, ast.AST):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)

        return node

    @_within_class_node
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST | None:
        skip_decorators(node, self.tokens_to_skip.decorators_to_skip)

        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        return self._handle_function_node(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST | None:
        return self._handle_function_node(node)

    @_within_function_node
    def _handle_function_node(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.AST | None:
        """Handles skips for both async/regular functions"""

        parsed_function: ast.FunctionDef | ast.AsyncFunctionDef | None = (
            self.generic_visit(node)  # type: ignore[assignment]
        )

        if (
            self.perf_optimizations.fold_simple_function_locals
            and parsed_function is not None
        ):
            locals_folder = _FunctionFoldableLocalsFinder(
                {a.arg for a in node.args.args}
            )
            locals_folder.visit(parsed_function)

            if locals_folder.foldable:
                _FunctionLocalsFolder(
                    self.perf_optimizations,
                    locals_folder.foldable,
                ).visit(parsed_function)

        return parsed_function

    @staticmethod
    def _body_is_only_pass(node_body: list[ast.stmt]) -> bool:
        return all(isinstance(n, ast.Pass) for n in node_body)

    def visit_If(self, node: ast.If) -> ast.AST | list[ast.stmt] | None:
        parsed_node: ast.AST = self.generic_visit(node)

        if isinstance(parsed_node, ast.If):
            if not parsed_node.orelse:
                if self._body_is_only_pass(parsed_node.body):
                    call_finder = _DanglingExprCallFinder(
                        self.perf_optimizations.functions_safe_to_exclude_in_test_expr
                    )
                    call_finder.visit(parsed_node.test)
                    return [ast.Expr(expr) for expr in call_finder.calls]

                if (
                    len(parsed_node.body) == 1
                    and isinstance(parsed_node.body[0], ast.If)
                    and not parsed_node.body[0].orelse
                ):
                    # These if conditions can be combine into one if
                    if isinstance(parsed_node.test, ast.BoolOp) and isinstance(
                        parsed_node.test.op, ast.And
                    ):
                        parsed_node.test.values.append(parsed_node.body[0].test)
                    else:
                        parsed_node.test = ast.BoolOp(
                            ast.And(), [parsed_node.test, parsed_node.body[0].test]
                        )

                    parsed_node.body = parsed_node.body[0].body

            elif self.code_to_skip.skip_useless_else and isinstance(
                parsed_node.body[-1], (ast.Raise, ast.Return)
            ):
                denested_else: list[ast.stmt] = parsed_node.orelse
                parsed_node.orelse = []
                denested_else.insert(0, parsed_node)
                return denested_else

        return parsed_node

    def visit_Call(self, node: ast.Call) -> ast.AST | None:
        if (
            self.perf_optimizations.assume_this_machine
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            function_call_key: str = f"{node.func.value.id}.{node.func.attr}"

            if function_call_key in machine_dependent_functions:
                return ast.Constant(machine_dependent_functions[function_call_key])

        return self.generic_visit(node)

    def _is_assign_of_folded_constant(self, target: ast.expr) -> bool:
        """Returns if node is assignment of a value that we are folding. In this case,
        there is no need to assign the value since its use"""

        return (
            isinstance(target, ast.Name)
            and target.id in self.perf_optimizations.names_to_fold
        )

    def _should_skip_function_assign(self, node: ast.Assign | ast.AnnAssign) -> bool:
        return (
            isinstance(node.value, ast.Call)
            and get_node_name(node.value.func) in self.tokens_to_skip.functions_to_skip
        )


class _DanglingExprCallFinder(AstNodeVisitorBase):
    """Finds all calls in a given dangling expression
    except for a subset of builtin functions that have
    no side effects."""

    __slots__ = ("calls", "excludes")

    def __init__(self, excludes: Iterable[str]) -> None:
        self.calls: list[ast.Call] = []
        self.excludes: Iterable[str] = excludes

    def visit_Call(self, node: ast.Call) -> ast.Call:
        if get_node_name(node.func) not in self.excludes:
            self.calls.append(node)

        return node


class _FunctionFoldableLocalsFinder(AstNodeVisitorBase):
    __slots__ = ("_excludes", "foldable")

    def __init__(self, excludes: set[str]) -> None:
        self.foldable: dict[str, ast.Constant] = {}
        self._excludes: set[str] = excludes

    def visit_Global(self, node: ast.Global) -> ast.Global:
        self._excludes |= set(node.names)
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.Nonlocal:
        self._excludes |= set(node.names)
        return node

    def visit_NamedExpr(self, node: ast.NamedExpr) -> ast.AST:
        self._handle_possible_foldable(node.target.id)
        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> ast.AST:

        targets: list[ast.expr]
        value: ast.AST | None
        if isinstance(node.targets[0], ast.Tuple):
            # For now, not considering any of these for folding
            targets = node.targets[0].elts
            value = None
        else:
            targets = node.targets
            value = node.value

        for target in targets:
            if isinstance(target, ast.Name):
                self._handle_possible_foldable(target.id, value)

        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:

        if isinstance(node.target, ast.Name):
            self._handle_possible_foldable(node.target.id, node.value)

        return self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST:

        if isinstance(node.target, ast.Name):
            self._handle_possible_foldable(node.target.id)

        return self.generic_visit(node)

    def _handle_possible_foldable(
        self, node_id: str, value: ast.AST | None = None
    ) -> None:
        if node_id in self.foldable:
            del self.foldable[node_id]
        elif (
            value is not None
            and node_id not in self._excludes
            and isinstance(value, ast.Constant)
            and (value.value is None or isinstance(value.value, int))
        ):
            self.foldable[node_id] = value

        self._excludes.add(node_id)


class _FunctionLocalsFolder(_OpFolder):
    __slots__ = ("folds",)

    def __init__(
        self,
        perf_optimizations: PerfOptimizationsConfig,
        folds: dict[str, ast.Constant],
    ) -> None:
        super().__init__(perf_optimizations, perf_optimizations)
        self.folds: dict[str, ast.Constant] = folds

    def visit_Assign(self, node: ast.Assign) -> ast.AST | None:

        new_targets = [
            target
            for target in node.targets
            if not isinstance(target, ast.Name) or target.id not in self.folds
        ]

        if not new_targets:
            return None

        node.targets = new_targets
        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:

        if isinstance(node.target, ast.Name) and node.target.id in self.folds:
            return None

        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.Name | ast.Constant:
        if node.id in self.folds:
            return self.folds[node.id]

        return node
