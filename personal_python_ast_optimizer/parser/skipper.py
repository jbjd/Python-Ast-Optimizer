import ast
import warnings
from collections.abc import Callable, Iterable
from enum import Enum
from typing import Self

from personal_python_ast_optimizer.config import (
    CodeToFoldConfig,
    CodeToSkipConfig,
    OptimizeConfig,
    OtherOptimizationsConfig,
    TokensToSkipConfig,
    TokenTypesToSkipConfig,
    TypeHintsToSkip,
)
from personal_python_ast_optimizer.futures import get_unneeded_futures
from personal_python_ast_optimizer.parser._base import (
    AstNodeTransformerBase,
    AstNodeVisitorBase,
)
from personal_python_ast_optimizer.parser.machine_info import (
    machine_dependent_attributes,
    machine_dependent_functions,
)
from personal_python_ast_optimizer.parser.utils import (
    exclude_imports,
    filter_imports,
    first_occurrence_of_type,
    get_node_name,
    is_overload_function,
    is_return_none,
    skip_base_classes,
    skip_decorators,
)


class _NodeContext(Enum):
    NONE = 0
    CLASS = 1
    FUNCTION = 2


class _OpFolder(AstNodeTransformerBase):
    __slots__ = ("code_to_fold", "other_optimizations")

    def __init__(
        self,
        code_to_fold: CodeToFoldConfig,
        other_optimizations: OtherOptimizationsConfig,
    ) -> None:
        super().__init__()
        self.code_to_fold: CodeToFoldConfig = code_to_fold
        self.other_optimizations: OtherOptimizationsConfig = other_optimizations

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        parsed_node: ast.AST = self.generic_visit(node)

        if isinstance(parsed_node, ast.BinOp):
            if (
                self.code_to_fold.fold_constants
                and isinstance(parsed_node.left, ast.Constant)
                and isinstance(parsed_node.right, ast.Constant)
            ):
                return self._ast_constants_operation(
                    parsed_node.left, parsed_node.right, parsed_node.op
                )

            if (
                self.other_optimizations.collection_concat_to_unpack
                and isinstance(parsed_node.op, ast.Add)
                and (
                    isinstance(parsed_node.left, (ast.Tuple, ast.List))
                    or isinstance(parsed_node.right, (ast.Tuple, ast.List))
                )
            ):
                if (
                    isinstance(parsed_node.left, ast.Tuple)
                    and isinstance(parsed_node.right, ast.Tuple)
                ) or (
                    isinstance(parsed_node.left, ast.List)
                    and isinstance(parsed_node.right, ast.List)
                ):
                    parsed_node.left.elts += parsed_node.right.elts
                elif isinstance(parsed_node.left, (ast.Tuple, ast.List)):
                    parsed_node.left.elts.append(ast.Starred(parsed_node.right))
                else:
                    parsed_node.right.elts.insert(0, ast.Starred(parsed_node.left))  # type: ignore[attr-defined]
                    return parsed_node.right

                return parsed_node.left

        return parsed_node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        parsed_node: ast.BoolOp = self.generic_visit(node)  # type: ignore[assignment]

        if isinstance(parsed_node.op, (ast.Or, ast.And)):
            # For And nodes left values that are Truthy and const can be removed
            # and vice versa
            remove_if: bool = isinstance(parsed_node.op, ast.And)
            self._left_remove_constants(parsed_node, remove_if)

            left: ast.AST = parsed_node.values[0]
            if isinstance(left, ast.Constant) and bool(left.value) is not remove_if:
                return left

        return parsed_node

    @staticmethod
    def _left_remove_constants(node: ast.BoolOp, remove_if: bool) -> None:
        index: int = 0
        end: int = len(node.values) - 1
        while index < end:
            left: ast.expr = node.values[index]
            if isinstance(left, ast.Constant) and bool(left.value) is remove_if:
                index += 1
            else:
                break

        if index > 0:
            node.values = node.values[index:]

    def visit_Compare(self, node: ast.Compare) -> ast.AST | None:
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

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        parsed_node = self.generic_visit(node)

        if isinstance(parsed_node, ast.UnaryOp) and isinstance(
            parsed_node.operand, ast.Constant
        ):
            if isinstance(parsed_node.op, ast.Not):
                return ast.Constant(not parsed_node.operand.value)
            if isinstance(parsed_node.op, ast.Invert):
                return ast.Constant(~parsed_node.operand.value)  # type: ignore[operator]
            if isinstance(parsed_node.op, ast.UAdd):
                return parsed_node.operand

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


class AstNodeSkipper(_OpFolder):
    __slots__ = (
        "_has_imports",
        "_node_context",
        "_simplified_named_tuple",
        "_skippable_futures",
        "code_to_skip",
        "module_name",
        "target_python_version",
        "token_types_to_skip",
        "tokens_to_skip",
    )

    def __init__(self, module_name: str, config: OptimizeConfig) -> None:
        super().__init__(config.code_to_fold, config.other_optimizations)

        self.module_name: str = module_name
        self.target_python_version: tuple[int, int] | None = (
            config.other_optimizations.target_python_version
        )
        self.code_to_skip: CodeToSkipConfig = config.code_to_skip
        self.token_types_to_skip: TokenTypesToSkipConfig = config.token_types_to_skip
        self.tokens_to_skip: TokensToSkipConfig = config.tokens_to_skip

        self._has_imports: bool = False
        self._simplified_named_tuple: bool = False
        self._node_context: _NodeContext = _NodeContext.NONE

        self._skippable_futures: list[str] = (
            get_unneeded_futures(self.target_python_version)
            if self.target_python_version is not None
            else []
        )

        if self.token_types_to_skip.skip_type_hints:
            self._skippable_futures.append("annotations")

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

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self.generic_visit(node)

        if self._simplified_named_tuple:
            import_to_update: ast.ImportFrom | None = None
            for n in node.body:
                if isinstance(n, ast.ImportFrom) and n.module == "collections":
                    if any(alias.name == "namedtuple" for alias in n.names):
                        break
                    if import_to_update is None:
                        import_to_update = n
            else:  # namedtuple was not already imported
                alias = ast.alias("namedtuple")
                if import_to_update is None:
                    node.body.insert(0, ast.ImportFrom("collections", [alias], 0))
                else:
                    import_to_update.names.append(alias)

        if self.code_to_skip.skip_unused_imports and self._has_imports:
            import_filter = UnusedImportSkipper(
                self.code_to_skip.unused_imports_to_preserve
            )
            import_filter.visit(node)

        self._warn_unused_skips()
        return node

    @_within_class_node
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST | None:
        if node.name in self.tokens_to_skip.classes_to_skip:
            return None

        skip_base_classes(node, self.tokens_to_skip.classes_to_skip)
        skip_decorators(node, self.tokens_to_skip.decorators_to_skip)

        if (
            self.other_optimizations.simplify_named_tuples
            and self._is_simple_named_tuple(node)
        ):
            self._simplified_named_tuple = True
            named_tuple = self._build_named_tuple(node)
            return ast.Assign([ast.Name(node.name)], named_tuple)

        return self.generic_visit(node)

    @staticmethod
    def _is_simple_named_tuple(node: ast.ClassDef) -> bool:
        return (
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

    @staticmethod
    def _build_named_tuple(node: ast.ClassDef) -> ast.Call:
        """Build what a namedtuple node would  be for a given
        class def inheriting from NamedTuple with only AnnAssigns in the body."""

        defaults: list[ast.expr]

        if node.body:
            defaults = [node.body[0].value] if node.body[0].value is not None else []  # type: ignore[attr-defined]

            for i in range(1, len(node.body)):
                assign: ast.AnnAssign = node.body[i]  # type: ignore[assignment]
                if assign.value is not None:
                    defaults.append(assign.value)
                elif node.body[i - 1].value is not None:  # type: ignore[attr-defined]
                    raise ValueError(
                        f'Non-default namedtuple "{node.name}" field '
                        f'"{get_node_name(assign.target)}" cannot follow default field'
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

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        return self._handle_function_node(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST | None:
        return self._handle_function_node(node)

    @_within_function_node
    def _handle_function_node(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.AST | None:
        """Handles skips for both async/regular functions"""
        if self._should_skip_function(node):
            return None

        if self.token_types_to_skip.skip_type_hints:
            node.returns = None

        skip_decorators(node, self.tokens_to_skip.decorators_to_skip)

        if node.body:
            last_body_node: ast.stmt = node.body[-1]
            if isinstance(last_body_node, ast.Return) and (
                is_return_none(last_body_node) or last_body_node.value is None
            ):
                node.body.pop()

        parsed_function: ast.FunctionDef | ast.AsyncFunctionDef | None = (
            self.generic_visit(node)  # type: ignore[assignment]
        )

        if (
            self.code_to_fold.fold_simple_function_locals
            and parsed_function is not None
        ):
            locals_folder = _FunctionFoldableLocalsFinder(
                {a.arg for a in node.args.args}
            )
            locals_folder.visit(parsed_function)

            if locals_folder.foldable:
                _FunctionLocalsFolder(
                    self.code_to_fold,
                    self.other_optimizations,
                    locals_folder.foldable,
                ).visit(parsed_function)

        return parsed_function

    def _should_skip_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> bool:
        """Determines if a function node should be skipped."""
        return node.name in self.tokens_to_skip.functions_to_skip or (
            self.code_to_skip.skip_overload_functions and is_overload_function(node)
        )

    def visit_Try(self, node: ast.Try) -> ast.AST | list[ast.stmt] | None:
        parsed_node = self.generic_visit(node)

        if isinstance(parsed_node, (ast.Try, ast.TryStar)) and self._body_is_only_pass(
            parsed_node.body
        ):
            return parsed_node.finalbody or None

        return parsed_node

    def visit_TryStar(self, node: ast.TryStar) -> ast.AST | list[ast.stmt] | None:
        parsed_node = self.generic_visit(node)

        if isinstance(parsed_node, (ast.Try, ast.TryStar)) and self._body_is_only_pass(
            parsed_node.body
        ):
            return parsed_node.finalbody or None

        return parsed_node

    @staticmethod
    def _body_is_only_pass(node_body: list[ast.stmt]) -> bool:
        return all(isinstance(n, ast.Pass) for n in node_body)

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST | None:
        if (
            isinstance(node.value, ast.Name)
            and self.other_optimizations.assume_this_machine
        ):
            attribute_key: str = f"{node.value.id}.{node.attr}"
            if attribute_key in machine_dependent_attributes:
                return ast.Constant(machine_dependent_attributes[attribute_key])

        return self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> ast.AST | None:
        """Skips assign if it is an assignment to a constant that is being folded"""
        if self._should_skip_function_assign(node):
            return None

        if isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            # TODO: handle skipping Starred vars
            target_elts = node.targets[0].elts
            original_target_len = len(target_elts)

            # Weird edge case: unpack contains a starred expression like *a,b = 1,2,3
            # Need to use negative indexes if a bad index comes after one of these
            starred_expr_index: int = first_occurrence_of_type(target_elts, ast.Starred)
            bad_indexes: list[int] = [
                (
                    i
                    if starred_expr_index == -1 or i < starred_expr_index
                    else original_target_len - i - 1
                )
                for i in range(len(target_elts))
                if self._is_assign_of_folded_constant(target_elts[i])
            ]

            node.targets[0].elts = [
                target for i, target in enumerate(target_elts) if i not in bad_indexes
            ]
            node.value.elts = [
                target
                for i, target in enumerate(node.value.elts)
                if i not in bad_indexes
            ]

            if not node.targets[0].elts:
                return None
            if len(node.targets[0].elts) == 1:
                node.targets = [node.targets[0].elts[0]]
            if len(node.value.elts) == 1:
                node.value = node.value.elts[0]
        else:
            new_targets: list[ast.expr] = [
                target
                for target in node.targets
                if not self._is_assign_of_folded_constant(target)
                and get_node_name(target) not in self.tokens_to_skip.variables_to_skip
            ]
            if not new_targets:
                return None

            node.targets = new_targets

        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        """Skips assign if it is an assignment to a constant that is being folded"""
        target_name: str = get_node_name(node.target)
        if (
            self._should_skip_function_assign(node)
            or target_name in self.tokens_to_skip.variables_to_skip
            or self._is_assign_of_folded_constant(node.target)
        ):
            return None

        parsed_node: ast.AnnAssign = self.generic_visit(node)  # type: ignore[assignment]

        if self.token_types_to_skip.skip_type_hints == TypeHintsToSkip.ALL or (
            self.token_types_to_skip.skip_type_hints
            == TypeHintsToSkip.ALL_BUT_CLASS_VARS
            and self._node_context != _NodeContext.CLASS
        ):
            if parsed_node.value is None:
                return None

            return ast.Assign([parsed_node.target], parsed_node.value)

        return parsed_node

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST | None:
        if get_node_name(node.target) in self.tokens_to_skip.variables_to_skip:
            return None

        return self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> ast.Import | None:
        exclude_imports(node, self.tokens_to_skip.module_imports_to_skip)

        if not node.names:
            return None

        self._has_imports = True
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        normalized_module_name: str = node.module or ""
        if normalized_module_name in self.tokens_to_skip.module_imports_to_skip:
            return None

        exclude_imports(node, self.tokens_to_skip.from_imports_to_skip)

        if node.module == "__future__" and self._skippable_futures:
            exclude_imports(node, self._skippable_futures)

        if not node.names:
            return None

        self._has_imports = True
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        """Extends super's implementation by adding constant folding"""
        if node.id in self.code_to_fold.vars_to_fold:
            constant_value = self.code_to_fold.vars_to_fold[node.id]

            return ast.Constant(constant_value)

        return node

    def visit_If(self, node: ast.If) -> ast.AST | list[ast.stmt] | None:
        parsed_node: ast.AST = self.generic_visit(node)

        if isinstance(parsed_node, ast.If):
            if isinstance(parsed_node.test, ast.Constant):
                if_body: list[ast.stmt] = (
                    parsed_node.body if parsed_node.test.value else parsed_node.orelse
                )
                return if_body or None

            if not parsed_node.orelse:
                if self._body_is_only_pass(parsed_node.body):
                    call_finder = _DanglingExprCallFinder(
                        self.other_optimizations.functions_safe_to_exclude_in_test_expr
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

    def visit_IfExp(self, node: ast.IfExp) -> ast.AST | None:
        parsed_node = self.generic_visit(node)

        if isinstance(parsed_node, ast.IfExp) and isinstance(
            parsed_node.test, ast.Constant
        ):
            return parsed_node.body if parsed_node.test.value else parsed_node.orelse

        return parsed_node

    def visit_While(self, node: ast.While) -> ast.AST | None:
        parsed_node = self.generic_visit(node)

        if isinstance(parsed_node, ast.While) and isinstance(
            parsed_node.test, ast.Constant
        ):
            if not parsed_node.test.value:
                return None

            # 1 is faster than True in python 2
            # They are the same in python 3, but less size
            parsed_node.test.value = 1

        return parsed_node

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if is_return_none(node):
            node.value = None
            return node

        return self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> ast.AST | None:
        return (
            None if self.token_types_to_skip.skip_asserts else self.generic_visit(node)
        )

    def visit_Pass(self, node: ast.Pass) -> None:  # type: ignore[override]  # noqa: ARG002
        """Always returns None. Pass is handled elsewhere only as needed.

        :param node: This is ignored"""
        return  # This could be toggleable

    def visit_Call(self, node: ast.Call) -> ast.AST | None:
        if (
            self.other_optimizations.assume_this_machine
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            function_call_key: str = f"{node.func.value.id}.{node.func.attr}"

            if function_call_key in machine_dependent_functions:
                return ast.Constant(machine_dependent_functions[function_call_key])

        if (
            self.code_to_skip.skip_typing_cast
            and isinstance(node.func, ast.Name)
            and node.func.id == "cast"
            and len(node.args) == 2  # noqa: PLR2004
        ):
            return self.generic_visit(node.args[1])

        return self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        if (
            isinstance(node.value, ast.Call)
            and get_node_name(node.value.func) in self.tokens_to_skip.functions_to_skip
        ):
            return None

        return self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> ast.AST:
        if self.token_types_to_skip.skip_type_hints:
            node.annotation = None
            return node

        return self.generic_visit(node)

    def visit_arguments(self, node: ast.arguments) -> ast.AST:
        if self.token_types_to_skip.skip_type_hints:
            if node.kwarg is not None:
                node.kwarg.annotation = None
            if node.vararg is not None:
                node.vararg.annotation = None

        return self.generic_visit(node)

    def _is_assign_of_folded_constant(self, target: ast.expr) -> bool:
        """Returns if node is assignment of a value that we are folding. In this case,
        there is no need to assign the value since its use"""

        return (
            isinstance(target, ast.Name) and target.id in self.code_to_fold.vars_to_fold
        )

    def _should_skip_function_assign(self, node: ast.Assign | ast.AnnAssign) -> bool:
        return (
            isinstance(node.value, ast.Call)
            and get_node_name(node.value.func) in self.tokens_to_skip.functions_to_skip
        )

    def _warn_unused_skips(self) -> None:
        for (
            token_type,
            not_found_tokens,
        ) in self.tokens_to_skip.get_missing_tokens_iter():
            warnings.warn(
                f"{self.module_name}: requested to skip {token_type} "
                f"{not_found_tokens} but was not found",
                stacklevel=2,
            )

    def visit_TypeVar(self, node: ast.TypeVar) -> ast.TypeVar | None:
        return None if self.token_types_to_skip.skip_generics_and_alias else node

    def visit_ParamSpec(self, node: ast.ParamSpec) -> ast.ParamSpec | None:
        return None if self.token_types_to_skip.skip_generics_and_alias else node

    def visit_TypeVarTuple(self, node: ast.TypeVarTuple) -> ast.TypeVarTuple | None:
        return None if self.token_types_to_skip.skip_generics_and_alias else node

    def visit_TypeAlias(self, node: ast.TypeAlias) -> ast.TypeAlias | None:
        return None if self.token_types_to_skip.skip_generics_and_alias else node


class UnusedImportSkipper(AstNodeTransformerBase):
    __slots__ = ("names_and_attrs",)

    def __init__(self, imports_to_preserve: Iterable[str]) -> None:
        super().__init__(reverse=True)
        self.names_and_attrs: set[str] = set(imports_to_preserve)

    def visit_Import(self, node: ast.Import) -> ast.Import | None:
        filter_imports(node, self.names_and_attrs)

        return node if node.names else None

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        if node.module != "__future__":
            filter_imports(node, self.names_and_attrs)

        return node if node.names else None

    def visit_Name(self, node: ast.Name) -> ast.Name:
        self.names_and_attrs.add(node.id)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self.names_and_attrs.add(node.attr)
        return self.generic_visit(node)


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
        code_to_fold: CodeToFoldConfig,
        other_optimizations: OtherOptimizationsConfig,
        folds: dict[str, ast.Constant],
    ) -> None:
        super().__init__(code_to_fold, other_optimizations)
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
