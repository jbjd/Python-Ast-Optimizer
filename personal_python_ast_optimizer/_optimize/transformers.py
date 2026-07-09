import ast
import sys
from collections.abc import Iterable
from enum import Enum
from typing import override

from personal_python_ast_optimizer._optimize._base import AstNodeTransformerBase
from personal_python_ast_optimizer.config import TypeHintsToSkip
from personal_python_ast_optimizer.futures import (
    FUTURE_IMPORT_NAME,
    Future,
    get_unneeded_futures,
)


class OptimizationPass(AstNodeTransformerBase):
    """Performs optimizations that may occur over multiple passes
    like constant folding or dead code elimination."""

    __slots__ = ("_did_work", "_passes", "fold_constants")

    def __init__(self, fold_constants: bool) -> None:
        self.fold_constants: bool = fold_constants
        self._passes: int = 0
        self._did_work: bool = False

    def has_work(self) -> bool:
        return self._passes < 1 or self._did_work

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self._passes += 1
        self._did_work = False
        node = self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> ast.AST | list[ast.stmt] | None:
        return self._handle_try(node)

    def visit_TryStar(self, node: ast.TryStar) -> ast.AST | list[ast.stmt] | None:
        return self._handle_try(node)

    def _handle_try(
        self, node: ast.Try | ast.TryStar
    ) -> ast.AST | list[ast.stmt] | None:
        parsed_node = self.generic_visit(node)

        if isinstance(parsed_node, (ast.Try, ast.TryStar)) and self._body_is_only_pass(
            parsed_node.body
        ):
            self._did_work = True
            return parsed_node.finalbody or None

        return parsed_node

    def visit_If(self, node: ast.If) -> ast.AST | list[ast.stmt] | None:
        return self._handle_if(node)

    def visit_IfExp(self, node: ast.IfExp) -> ast.AST | None:
        return self._handle_if(node)

    def _handle_if(self, node: ast.If | ast.IfExp) -> ast.AST | list[ast.stmt] | None:
        parsed_node: ast.AST = self.generic_visit(node)

        if isinstance(parsed_node, (ast.If, ast.IfExp)) and isinstance(
            parsed_node.test, ast.Constant
        ):
            if_body: list[ast.stmt] = (
                parsed_node.body if parsed_node.test.value else parsed_node.orelse
            )
            return if_body or None

        return parsed_node

    def visit_While(self, node: ast.While) -> ast.AST | None:
        parsed_node = self.generic_visit(node)

        if (
            isinstance(parsed_node, ast.While)
            and isinstance(parsed_node.test, ast.Constant)
            and not parsed_node.test.value
        ):
            return None

        return parsed_node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        if isinstance(node.op, (ast.Or, ast.And)):
            # For And nodes left values that are Truthy and const can be removed
            # and vice versa
            remove_if: bool = isinstance(node.op, ast.And)

            index: int = 0
            end: int = len(node.values) - 1
            while index < end:
                left: ast.expr = node.values[index]
                if isinstance(left, ast.Constant) and bool(left.value) is remove_if:
                    index += 1
                else:
                    break
            else:  # all values before last are skippable
                self._did_work = True
                return node.values[-1]

            # 'False and some_func()' can be simplified to just 'False'
            left: ast.AST = node.values[index]
            if isinstance(left, ast.Constant) and bool(left.value) is not remove_if:
                self._did_work = True
                return left

            if index > 0:
                self._did_work = True
                node.values = node.values[index:]

        return node

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        parsed_node: ast.AST = self.generic_visit(node)

        if isinstance(parsed_node, ast.UnaryOp) and isinstance(
            parsed_node.operand, ast.Constant
        ):
            if isinstance(parsed_node.op, ast.Not):
                self._did_work = True
                return ast.Constant(not parsed_node.operand.value)
            if isinstance(parsed_node.op, ast.UAdd):
                self._did_work = True
                return parsed_node.operand
            if sys.version_info < (3, 16) and isinstance(parsed_node.op, ast.Invert):
                self._did_work = True
                return ast.Constant(~parsed_node.operand.value)  # type: ignore[operator]

        return parsed_node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        parsed_node: ast.AST = self.generic_visit(node)

        if (
            self.fold_constants
            and isinstance(parsed_node, ast.BinOp)
            and isinstance(parsed_node.left, ast.Constant)
            and isinstance(parsed_node.right, ast.Constant)
        ):
            self._did_work = True
            return self._ast_constants_operation(
                parsed_node.left, parsed_node.right, parsed_node.op
            )

        return parsed_node

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        parsed_node = self.generic_visit(node)

        if (
            isinstance(parsed_node, ast.Compare)
            and isinstance(parsed_node.left, ast.Constant)
            and len(parsed_node.comparators) == 1
            and isinstance(parsed_node.comparators[0], ast.Constant)
        ):
            self._did_work = True
            return self._ast_constants_operation(
                parsed_node.left, parsed_node.comparators[0], parsed_node.ops[0]
            )

        return parsed_node

    @staticmethod
    def _ast_constants_operation(  # noqa: C901, PLR0912
        left: ast.Constant,
        right: ast.Constant,
        operation: ast.operator | ast.cmpop,
    ) -> ast.Constant:
        """Given two ast.Constant values, performs an operation on their underlying
        values and returns a new ast.Constant of the new value.

        :param left: ast.Constant in the left of the operation.
        :param right: ast.Constant in the right of the operation.
        :param operation: One of the ast classes representing an operation."""

        left_value: ast._ConstantValue = left.value
        right_value: ast._ConstantValue = right.value
        result: ast._ConstantValue

        match operation:
            case ast.Add():
                result = left_value + right_value  # type: ignore[operator]
            case ast.Sub():
                result = left_value - right_value  # type: ignore[operator]
            case ast.Mult():
                result = left_value * right_value  # type: ignore[operator]
            case ast.Div():
                result = left_value / right_value  # type: ignore[operator]
            case ast.FloorDiv():
                result = left_value // right_value  # type: ignore[operator]
            case ast.Mod():
                result = left_value % right_value  # type: ignore[operator]
            case ast.Pow():
                result = left_value**right_value  # type: ignore[operator]
            case ast.LShift():
                result = left_value << right_value  # type: ignore[operator]
            case ast.RShift():
                result = left_value >> right_value  # type: ignore[operator]
            case ast.BitOr():
                result = left_value | right_value  # type: ignore[operator]
            case ast.BitXor():
                result = left_value ^ right_value  # type: ignore[operator]
            case ast.BitAnd():
                result = left_value & right_value  # type: ignore[operator]
            case ast.Eq():
                result = left_value == right_value
            case ast.NotEq():
                result = left_value != right_value
            case ast.Lt():
                result = left_value < right_value  # type: ignore[operator]
            case ast.LtE():
                result = left_value <= right_value  # type: ignore[operator]
            case ast.Gt():
                result = left_value > right_value  # type: ignore[operator]
            case ast.GtE():
                result = left_value >= right_value  # type: ignore[operator]
            case ast.Is():
                result = left_value is right_value
            case ast.IsNot():
                result = left_value is not right_value
            case _:
                raise ValueError(f"Invalid operation: {operation.__class__.__name__}")

        return ast.Constant(result)

    @staticmethod
    def _body_is_only_pass(node_body: list[ast.AST]) -> bool:
        return all(isinstance(n, ast.Pass) for n in node_body)


class _NodeContext(Enum):
    NONE = 0
    CLASS = 1
    FUNCTION = 2


class FirstPassOptimizer(OptimizationPass):
    """Removes All nodes that only need to be removed once and can't be
    optimized into removal later. Intened to be called once as a first pass."""

    __slots__ = (
        "_node_context",
        "_unneeded_futures",
        "skip_asserts",
        "skip_dangling_expressions",
        "skip_generics",
        "skip_overload_functions",
        "skip_type_hints",
        "skip_typing_cast",
    )

    def __init__(
        self,
        fold_constants: bool,
        skip_dangling_expressions: bool,
        skip_type_hints: TypeHintsToSkip,
        skip_generics: bool,
        skip_asserts: bool,
        skip_typing_cast: bool,
        skip_overload_functions: bool,
        target_python_version: tuple[int, int],
    ) -> None:
        super().__init__(fold_constants)
        self.skip_dangling_expressions: bool = skip_dangling_expressions
        self.skip_type_hints: TypeHintsToSkip = skip_type_hints
        self.skip_generics: bool = skip_generics and bool(skip_type_hints)
        self.skip_asserts: bool = skip_asserts
        self.skip_typing_cast: bool = skip_typing_cast
        self.skip_overload_functions: bool = skip_overload_functions
        self._node_context: _NodeContext = _NodeContext.NONE

        self._unneeded_futures: list[Future] = get_unneeded_futures(
            target_python_version
        )
        if skip_type_hints:
            self._unneeded_futures.append("annotations")

    def visit_AsyncFunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._handle_function(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._handle_function(node)

    def _handle_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.AST | None:
        if self.skip_overload_functions and self._is_overload_function(node):
            return None

        if self.skip_type_hints:
            node.returns = None

        return self._visit_with_context(node, _NodeContext.FUNCTION)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        return self._visit_with_context(node, _NodeContext.CLASS)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        if node.module == FUTURE_IMPORT_NAME:
            node.names = [
                alias
                for alias in node.names
                if alias.name not in self._unneeded_futures
            ]

        return node if node.names else None

    def visit_arg(self, node: ast.arg) -> ast.arg:
        if self.skip_type_hints:
            node.annotation = None

        return node

    def visit_Call(self, node: ast.Call) -> ast.AST | None:
        if (
            self.skip_typing_cast
            and isinstance(node.func, ast.Name)
            and node.func.id == "cast"
            and len(node.args) == 2  # noqa: PLR2004
        ):
            return self.generic_visit(node.args[1])

        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        if self.skip_type_hints == TypeHintsToSkip.ALL or (
            self.skip_type_hints == TypeHintsToSkip.ALL_BUT_CLASS_VARS
            and self._node_context != _NodeContext.CLASS
        ):
            return (
                None
                if node.value is None
                else self.generic_visit(ast.Assign([node.target], node.value))
            )

        return self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if isinstance(node.value, ast.Constant) and node.value.value is None:
            node.value = None
            return node

        return self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> ast.AST | None:
        return None if self.skip_asserts else self.generic_visit(node)

    def visit_TypeVar(self, node: ast.TypeVar) -> ast.TypeVar | None:
        return None if self.skip_generics else self.generic_visit(node)

    def visit_ParamSpec(self, node: ast.ParamSpec) -> ast.ParamSpec | None:
        return None if self.skip_generics else self.generic_visit(node)

    def visit_TypeVarTuple(self, node: ast.TypeVarTuple) -> ast.TypeVarTuple | None:
        return None if self.skip_generics else self.generic_visit(node)

    def visit_TypeAlias(self, node: ast.TypeAlias) -> ast.TypeAlias | None:
        return None if self.skip_generics else self.generic_visit(node)

    # Removes duplicate passes. Super class handles adding them back if needed
    # such as an empty if body
    def visit_Pass(self, _: ast.Pass) -> None:
        return None

    def _visit_with_context(self, node: ast.AST, context: _NodeContext) -> ast.AST:
        previous_value: _NodeContext = self._node_context
        self._node_context = context
        try:
            return self.generic_visit(node)
        finally:
            self._node_context = previous_value

    @staticmethod
    def _is_overload_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        return (
            len(node.decorator_list) == 1
            and isinstance(node.decorator_list[0], ast.Name)
            and node.decorator_list[0].id == "overload"
        )


class LastPassOptimizer(AstNodeTransformerBase):
    """Removes unused import nodes from AST and other final touches."""

    __slots__ = ("_names_and_attrs", "skip_unused_imports")

    def __init__(
        self, skip_unused_imports: bool, imports_to_preserve: Iterable[str]
    ) -> None:
        self.skip_unused_imports: bool = skip_unused_imports
        self._names_and_attrs: set[str] = set(imports_to_preserve)

    def visit_Import(self, node: ast.Import) -> ast.Import | None:
        if not self.skip_unused_imports:
            return node

        self._filter_imports(node)

        return node if node.names else None

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        if not self.skip_unused_imports:
            return node

        if node.module != "__future__":
            self._filter_imports(node)

        return node if node.names else None

    def visit_Name(self, node: ast.Name) -> ast.Name:
        self._names_and_attrs.add(node.id)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self._names_and_attrs.add(node.attr)
        return self.generic_visit(node)

    def _filter_imports(self, node: ast.Import | ast.ImportFrom) -> None:
        node.names = [
            alias
            for alias in node.names
            if (alias.asname or alias.name) in self._names_and_attrs
        ]

    def visit_While(self, node: ast.While) -> ast.AST:
        if isinstance(node.test, ast.Constant) and node.test.value:
            # 1 is faster than True in python 2
            # They are the same in python 3, but less size
            node.test.value = 1

        return self.generic_visit(node)

    @override
    @staticmethod
    def _alter_node_list_visit_order(ast_list: list[ast.AST]) -> list[ast.AST]:
        return reversed(ast_list)
