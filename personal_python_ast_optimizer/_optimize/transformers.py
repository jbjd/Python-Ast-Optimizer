"""Transformer classes to optimize Python ASTs."""

import ast
import sys
from collections.abc import Iterable
from enum import Enum
from typing import override

from personal_python_ast_optimizer._optimize.base import AstNodeTransformerBase
from personal_python_ast_optimizer._optimize.utils import (
    TokensTracker,
    get_full_attribute_id,
    get_name_or_full_attribute_id,
    is_return_literal_none,
)
from personal_python_ast_optimizer.config import TypeHintsToSkip


class OptimizationPass(AstNodeTransformerBase):
    """Performs optimizations that may occur over multiple passes
    like constant folding or dead code elimination."""

    __slots__ = ("additional_pass_needed", "fold_constants")

    def __init__(self, fold_constants: bool) -> None:
        self.fold_constants: bool = fold_constants
        self.additional_pass_needed: bool = False

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self.additional_pass_needed = False
        return self.generic_visit(node)

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
            return parsed_node.finalbody or None

        return parsed_node

    def visit_If(self, node: ast.If) -> ast.AST | list[ast.stmt] | None:
        parsed_node: ast.AST = self.generic_visit(node)

        if isinstance(parsed_node, ast.If):
            if isinstance(parsed_node.test, ast.Constant):
                if_body: list[ast.stmt] = (
                    parsed_node.body if parsed_node.test.value else parsed_node.orelse
                )
                return if_body or None

            if (
                not parsed_node.orelse
                and len(parsed_node.body) == 1
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

        return parsed_node

    def visit_IfExp(self, node: ast.IfExp) -> ast.AST | None:
        parsed_node: ast.AST = self.generic_visit(node)

        if isinstance(parsed_node, ast.IfExp) and isinstance(
            parsed_node.test, ast.Constant
        ):
            if_body: ast.expr = (
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
                current_node: ast.expr = node.values[index]
                if (
                    isinstance(current_node, ast.Constant)
                    and bool(current_node.value) is remove_if
                ):
                    index += 1
                else:
                    break
            else:  # all values before last are skippable
                return node.values[-1]

            # 'False and some_func()' can be simplified to just 'False'
            left_value: ast.AST = node.values[index]
            if (
                isinstance(left_value, ast.Constant)
                and bool(left_value.value) is not remove_if
            ):
                return left_value

            if index > 0:
                node.values = node.values[index:]

        return node

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        parsed_node: ast.AST = self.generic_visit(node)

        if isinstance(parsed_node, ast.UnaryOp) and isinstance(
            parsed_node.operand, ast.Constant
        ):
            if isinstance(parsed_node.op, ast.Not):
                return ast.Constant(not parsed_node.operand.value)
            if isinstance(parsed_node.op, ast.UAdd):
                return parsed_node.operand
            if sys.version_info < (3, 16) and isinstance(parsed_node.op, ast.Invert):
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
    def _body_is_only_pass(node_body: Iterable[ast.AST]) -> bool:
        return all(isinstance(n, ast.Pass) for n in node_body)


class _NodeContext(Enum):
    NONE = 0
    CLASS = 1
    FUNCTION = 2


class _SimplifyNamedTuple(Enum):
    NO = 0
    YES = 1
    FOUND = 2

    def __bool__(self) -> bool:
        return self != _SimplifyNamedTuple.NO


class FirstPassOptimizer(OptimizationPass):
    """Removes All nodes that only need to be removed once and can't be
    optimized into removal later. Intened to be called once as a first pass."""

    __slots__ = (
        "_node_context",
        "_unneeded_futures",
        "collection_concat_to_unpack",
        "simplify_named_tuple",
        "skip_asserts",
        "skip_dangling_expressions",
        "skip_generics_and_alias",
        "skip_overload_functions",
        "skip_type_hints",
        "skip_typing_cast",
        "skip_useless_else",
        "tokens_to_skip",
    )

    def __init__(
        self,
        tokens_to_skip: TokensTracker,
        fold_constants: bool,
        collection_concat_to_unpack: bool,
        simplify_named_tuple: bool,
        skip_dangling_expressions: bool,
        skip_type_hints: TypeHintsToSkip,
        skip_generics_and_alias: bool,
        skip_asserts: bool,
        skip_typing_cast: bool,
        skip_overload_functions: bool,
        skip_useless_else: bool,
    ) -> None:
        super().__init__(fold_constants)
        self.collection_concat_to_unpack: bool = collection_concat_to_unpack
        self.simplify_named_tuple: _SimplifyNamedTuple = _SimplifyNamedTuple(
            simplify_named_tuple
        )
        self.tokens_tracker: TokensTracker = tokens_to_skip
        self.skip_dangling_expressions: bool = skip_dangling_expressions
        self.skip_type_hints: TypeHintsToSkip = skip_type_hints
        self.skip_generics_and_alias: bool = skip_generics_and_alias and bool(
            skip_type_hints
        )
        self.skip_asserts: bool = skip_asserts
        self.skip_typing_cast: bool = skip_typing_cast
        self.skip_overload_functions: bool = skip_overload_functions
        self.skip_useless_else: bool = skip_useless_else
        self._node_context: _NodeContext = _NodeContext.NONE

    @override
    def _on_visited_node_add_to_new_values(
        self, new_nodes: list[ast.AST], node: ast.AST
    ) -> None:
        if (
            self.skip_dangling_expressions
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
        ):
            return

        super()._on_visited_node_add_to_new_values(new_nodes, node)

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self.generic_visit(node)

        if self.simplify_named_tuple == _SimplifyNamedTuple.FOUND:
            handled: bool = False
            alias = ast.alias("namedtuple")
            for n in node.body:
                if isinstance(n, ast.ImportFrom) and n.module == "collections":
                    if not any(alias.name == "namedtuple" for alias in n.names):
                        n.names.append(alias)
                    handled = True
                    break

            if not handled:
                node.body.insert(0, ast.ImportFrom("collections", [alias], 0))

        return node

    def visit_AsyncFunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        return self._handle_function(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        return self._handle_function(node)

    def _handle_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.AST | None:
        if (
            self.skip_overload_functions and self._is_overload_function(node)
        ) or self.tokens_tracker.functions_to_skip.has(node.name):
            return None

        if self.skip_type_hints:
            node.returns = None

        self._skip_decorators(node)

        parsed_node: ast.AST | None = self._visit_with_context(
            node, _NodeContext.FUNCTION
        )

        if (
            isinstance(parsed_node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and isinstance(parsed_node.body[-1], ast.Return)
            and (
                is_return_literal_none(parsed_node.body[-1])
                or parsed_node.body[-1].value is None
            )
        ):
            if len(parsed_node.body) > 1:
                parsed_node.body.pop()
            else:
                parsed_node.body[0] = ast.Pass()

        return parsed_node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST | None:
        if self.tokens_tracker.classes_to_skip:
            if self.tokens_tracker.classes_to_skip.has(node.name):
                return None

            node.bases = [
                base
                for base in node.bases
                if not self.tokens_tracker.classes_to_skip.has(
                    get_name_or_full_attribute_id(base)
                )
            ]

        self._skip_decorators(node)

        parsed_node: ast.AST | None = self._visit_with_context(node, _NodeContext.CLASS)

        if (
            self.simplify_named_tuple
            and isinstance(parsed_node, ast.ClassDef)
            and (
                len(node.bases) == 1
                and isinstance(node.bases[0], ast.Name)
                and node.bases[0].id == "NamedTuple"
                and not node.keywords
                and not node.decorator_list
                and all(
                    isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                    for n in node.body
                )
            )
        ):
            self.simplify_named_tuple = _SimplifyNamedTuple.FOUND
            named_tuple: ast.Call = self._build_named_tuple(node)
            return ast.Assign([ast.Name(node.name)], named_tuple)

        return parsed_node

    def visit_If(self, node: ast.If) -> ast.AST | list[ast.stmt] | None:
        parsed_node: ast.AST = super().visit_If(node)

        if (
            isinstance(parsed_node, ast.If)
            and self.skip_useless_else
            and isinstance(parsed_node.body[-1], (ast.Raise, ast.Return))
        ):
            denested_else: list[ast.stmt] = parsed_node.orelse
            parsed_node.orelse = []
            return [parsed_node, *denested_else]

        return parsed_node

    def visit_Import(self, node: ast.Import) -> ast.AST | None:
        node.names = [
            alias
            for alias in node.names
            if not self.tokens_tracker.module_imports_to_skip.has(
                alias.name if alias.asname is None else alias.asname
            )
        ]

        return node if node.names else None

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST | None:
        node.names = [
            alias
            for alias in node.names
            if not self.tokens_tracker.from_imports_to_skip.has(
                (
                    ("." * node.level) + (node.module or ""),
                    alias.name if alias.asname is None else alias.asname,
                )
            )
        ]

        return node if node.names else None

    def visit_arg(self, node: ast.arg) -> ast.AST | None:
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

    def visit_Assign(self, node: ast.Assign) -> ast.AST | None:
        node.targets = [
            t
            for t in node.targets
            if not self.tokens_tracker.names_to_fold.has(
                t_name := get_name_or_full_attribute_id(t)
            )
            and not self.tokens_tracker.assignments_to_skip.has(t_name)
        ]

        return self.generic_visit(node) if node.targets else None

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        node_name: str | None = get_name_or_full_attribute_id(node.target)
        if self.tokens_tracker.names_to_fold.has(
            node_name
        ) or self.tokens_tracker.assignments_to_skip.has(node_name):
            return None

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

    def visit_Return(self, node: ast.Return) -> ast.AST | None:
        if is_return_literal_none(node):
            node.value = None
            return node

        return self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> ast.AST | None:
        return None if self.skip_asserts else self.generic_visit(node)

    def visit_TypeVar(self, node: ast.TypeVar) -> ast.AST | None:
        return None if self.skip_generics_and_alias else self.generic_visit(node)

    def visit_ParamSpec(self, node: ast.ParamSpec) -> ast.AST | None:
        return None if self.skip_generics_and_alias else self.generic_visit(node)

    def visit_TypeVarTuple(self, node: ast.TypeVarTuple) -> ast.AST | None:
        return None if self.skip_generics_and_alias else self.generic_visit(node)

    def visit_TypeAlias(self, node: ast.TypeAlias) -> ast.AST | None:
        return None if self.skip_generics_and_alias else self.generic_visit(node)

    # Removes duplicate passes. Super class handles adding them back if needed
    # such as an empty if body
    def visit_Pass(self, _: ast.Pass) -> ast.AST | None:
        return None

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        if isinstance(
            node.value, ast.Call
        ) and self.tokens_tracker.functions_to_skip.has(
            get_name_or_full_attribute_id(node.value.func)
        ):
            node.value = ast.Constant(None)
            return node

        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST | None:
        parsed_node: ast.AST | None = super().visit_BinOp(node)

        if (
            isinstance(parsed_node, ast.BinOp)
            and isinstance(parsed_node.op, ast.Add)
            and (
                isinstance(parsed_node.left, (ast.Tuple, ast.List))
                or isinstance(parsed_node.right, (ast.Tuple, ast.List))
            )
        ):
            if type(parsed_node.left) is type(parsed_node.right):
                parsed_node.left.elts += parsed_node.right.elts
                return parsed_node.left

            if self.collection_concat_to_unpack:
                if isinstance(parsed_node.left, (ast.Tuple, ast.List)):
                    parsed_node.left.elts.append(ast.Starred(parsed_node.right))
                    return parsed_node.left

                parsed_node.right.elts.insert(0, ast.Starred(parsed_node.left))  # type: ignore[attr-defined]
                return parsed_node.right

        return parsed_node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute | ast.Constant:
        full_attr_id: str = get_full_attribute_id(node)
        if self.tokens_tracker.names_to_fold.has(full_attr_id):
            return ast.Constant(self.tokens_tracker.names_to_fold.get(full_attr_id))

        return node

    def visit_Name(self, node: ast.Name) -> ast.Name | ast.Constant:
        if self.tokens_tracker.names_to_fold.has(node.id):
            return ast.Constant(self.tokens_tracker.names_to_fold.get(node.id))

        return node

    def _visit_with_context(
        self, node: ast.AST, context: _NodeContext
    ) -> ast.AST | None:
        previous_value: _NodeContext = self._node_context
        self._node_context = context
        try:
            return self.generic_visit(node)
        finally:
            self._node_context = previous_value

    def _skip_decorators(
        self,
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        if self.tokens_tracker.decorators_to_skip:
            node.decorator_list = [
                n
                for n in node.decorator_list
                if not self.tokens_tracker.decorators_to_skip.has(
                    get_name_or_full_attribute_id(n)
                )
            ]

    @staticmethod
    def _build_named_tuple(node: ast.ClassDef) -> ast.Call:

        defaults: list[ast.expr]
        if node.body:
            defaults = [node.body[0].value] if node.body[0].value is not None else []  # type: ignore[attr-defined]

            for i in range(1, len(node.body)):
                assign: ast.AnnAssign = node.body[i]  # type: ignore[assignment]
                if assign.value is not None:
                    defaults.append(assign.value)
                elif node.body[i - 1].value is not None:  # type: ignore[attr-defined]
                    raise ValueError(
                        f'namedtuple "{node.name}" has '
                        "non-default following a default field"
                    )

        else:
            defaults = []

        keywords: list[ast.keyword] = (
            [ast.keyword("defaults", ast.List(defaults))] if defaults else []
        )

        return ast.Call(
            ast.Name("namedtuple"),
            [
                ast.Constant(node.name),
                ast.List([ast.Constant(n.target.id) for n in node.body]),  # type: ignore[attr-defined]
            ],
            keywords,
        )

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

    @override
    def _on_visited_node_add_to_new_values(
        self, new_nodes: list[ast.AST], node: ast.AST
    ) -> None:
        if new_nodes:
            previous_node: ast.AST = new_nodes[-1]
            if (
                isinstance(node, ast.Import) and isinstance(previous_node, ast.Import)
            ) or (
                isinstance(node, ast.ImportFrom)
                and isinstance(previous_node, ast.ImportFrom)
                and node.module == previous_node.module
                and node.level == previous_node.level
            ):
                node.names += previous_node.names
                new_nodes[-1] = node
                return

        super()._on_visited_node_add_to_new_values(new_nodes, node)

    @override
    @staticmethod
    def _alter_node_list_visit_order(ast_list: list[ast.AST]) -> Iterable[ast.AST]:
        return reversed(ast_list)

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
