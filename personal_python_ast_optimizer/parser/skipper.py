import ast
import warnings

from personal_python_ast_optimizer.futures import get_unneeded_futures
from personal_python_ast_optimizer.parser.config import (
    OptimizationsConfig,
    SkipConfig,
    TokensConfig,
    TokenTypesConfig,
)
from personal_python_ast_optimizer.parser.machine_info import (
    machine_dependent_attributes,
    machine_dependent_functions,
)
from personal_python_ast_optimizer.parser.utils import (
    first_occurrence_of_type,
    get_node_name,
    is_overload_function,
    is_return_none,
    remove_duplicate_slots,
    skip_base_classes,
    skip_dangling_expressions,
    skip_decorators,
)


class AstNodeSkipper(ast.NodeTransformer):

    __slots__ = (
        "_skippable_futures",
        "_within_class",
        "_within_function",
        "module_name",
        "warn_unusual_code",
        "target_python_version",
        "optimizations_config",
        "token_types_config",
        "tokens_config",
    )

    def __init__(self, config: SkipConfig) -> None:
        self.module_name: str = config.module_name
        self.warn_unusual_code: bool = config.warn_unusual_code
        self.target_python_version: tuple[int, int] | None = (
            config.target_python_version
        )
        self.optimizations_config: OptimizationsConfig = config.optimizations_config
        self.token_types_config: TokenTypesConfig = config.token_types_config
        self.tokens_config: TokensConfig = config.tokens_config

        self._within_class: bool = False
        self._within_function: bool = False

        self._skippable_futures: list[str] = (
            get_unneeded_futures(self.target_python_version)
            if self.target_python_version is not None
            else []
        )

        if self.token_types_config.skip_type_hints:
            self._skippable_futures.append("annotations")

    @staticmethod
    def _within_class_node(function):
        def wrapper(self: "AstNodeSkipper", *args, **kwargs) -> ast.AST | None:
            self._within_class = True
            try:
                return function(self, *args, **kwargs)
            finally:
                self._within_class = False

        return wrapper

    @staticmethod
    def _within_function_node(function):
        def wrapper(self: "AstNodeSkipper", *args, **kwargs) -> ast.AST | None:
            self._within_function = True
            try:
                return function(self, *args, **kwargs)
            finally:
                self._within_function = False

        return wrapper

    def generic_visit(self, node) -> ast.AST:
        """Modified version of super class's generic_visit
        to extend functionality"""
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                new_values = []
                self._combine_imports(old_value)
                for value in old_value:
                    if isinstance(value, ast.AST):
                        value = self.visit(value)
                        if value is None:
                            continue
                        elif not isinstance(value, ast.AST):
                            new_values.extend(value)
                            continue
                    new_values.append(value)

                if (
                    field == "body"
                    and not new_values
                    and not isinstance(node, ast.Module)
                ):
                    new_values = [ast.Pass()]

                old_value[:] = new_values

            elif isinstance(old_value, ast.AST):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)
        return node

    @staticmethod
    def _combine_imports(body: list) -> None:
        if not body:
            return

        new_body = [body[0]]

        for i in range(1, len(body)):
            this_node = body[i]
            last_node = new_body[-1]

            if isinstance(this_node, ast.Import) and isinstance(last_node, ast.Import):
                last_node.names += this_node.names
            elif (
                isinstance(this_node, ast.ImportFrom)
                and isinstance(last_node, ast.ImportFrom)
                and this_node.module == last_node.module
                and this_node.level == last_node.level
            ):
                last_node.names += this_node.names
            else:
                new_body.append(this_node)

        body[:] = new_body

    def visit_Module(self, node: ast.Module) -> ast.AST:
        if not self._has_code_to_skip():
            return node

        if self.token_types_config.skip_dangling_expressions:
            skip_dangling_expressions(node)

        try:
            return self.generic_visit(node)
        finally:
            self._warn_unused_skips()

    @_within_class_node
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST | None:
        if (
            node.name in self.tokens_config.classes_to_skip
            or node.name in self.optimizations_config.enums_to_fold
        ):
            return None

        if self._use_version_optimization((3, 0)):
            skip_base_classes(node, ["object"])

        if self.token_types_config.skip_dangling_expressions:
            skip_dangling_expressions(node)

        skip_base_classes(node, self.tokens_config.classes_to_skip)
        skip_decorators(node, self.tokens_config.decorators_to_skip)

        return self.generic_visit(node)

    @_within_function_node
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        return self._handle_function_node(node)

    @_within_function_node
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST | None:
        return self._handle_function_node(node)

    def _should_skip_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> bool:
        """If a function node should be skipped"""
        return node.name in self.tokens_config.functions_to_skip or (
            self.token_types_config.skip_overload_functions
            and is_overload_function(node)
        )

    def _handle_function_node(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.AST | None:
        """Handles skips for both async/regular functions"""
        if self._should_skip_function(node):
            return None

        if self.token_types_config.skip_type_hints:
            node.returns = None

        if self.token_types_config.skip_dangling_expressions:
            skip_dangling_expressions(node)

        skip_decorators(node, self.tokens_config.decorators_to_skip)

        if node.body:
            last_body_node: ast.stmt = node.body[-1]
            if isinstance(last_body_node, ast.Return) and (
                is_return_none(last_body_node) or last_body_node.value is None
            ):
                node.body = node.body[:-1]

        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST | None:
        if isinstance(node.value, ast.Name):
            if node.attr in self.optimizations_config.enums_to_fold.get(
                node.value.id, []
            ):
                return self._get_enum_value_as_AST(node.value.id, node.attr)

            if self.optimizations_config.assume_this_machine:
                attribute_key: str = f"{node.value.id}.{node.attr}"
                if attribute_key in machine_dependent_attributes:
                    return ast.Constant(machine_dependent_attributes[attribute_key])

        if isinstance(
            node.value, ast.Attribute
        ) and node.attr in self.optimizations_config.enums_to_fold.get(
            node.value.attr, []
        ):
            return self._get_enum_value_as_AST(node.value.attr, node.attr)

        return self.generic_visit(node)

    def _get_enum_value_as_AST(self, class_name: str, value_name: str) -> ast.Constant:
        return ast.Constant(
            self.optimizations_config.enums_to_fold[class_name][value_name].value
        )

    def visit_Assign(self, node: ast.Assign) -> ast.AST | None:
        """Skips assign if it is an assignment to a constant that is being folded"""
        if self._should_skip_function_assign(node):
            return None

        # TODO: Currently if a.b.c.d only "c" and "d" are checked
        var_name: str = get_node_name(node.targets[0])
        parent_var_name: str = get_node_name(getattr(node.targets[0], "value", object))

        if (
            var_name in self.tokens_config.variables_to_skip
            or parent_var_name in self.tokens_config.variables_to_skip
        ):
            return None

        new_targets: list[ast.expr] = [
            target
            for target in node.targets
            if not self._is_assign_of_folded_constant(target, node.value)
        ]
        if not new_targets:
            return None

        if (
            self._within_class
            and len(node.targets) == 1
            and get_node_name(node.targets[0]) == "__slots__"
        ):
            remove_duplicate_slots(node, self.warn_unusual_code)

        node.targets = new_targets

        if isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
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
                if self._is_assign_of_folded_constant(
                    target_elts[i], node.value.elts[i]
                )
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

        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        """Skips assign if it is an assignment to a constant that is being folded"""
        if (
            self._should_skip_function_assign(node)
            or get_node_name(node.target) in self.tokens_config.variables_to_skip
            or self._is_assign_of_folded_constant(node.target, node.value)
        ):
            return None

        if self._within_class and get_node_name(node.target) == "__slots__":
            remove_duplicate_slots(node, self.warn_unusual_code)

        parsed_node: ast.AnnAssign = self.generic_visit(node)  # type: ignore

        if self.token_types_config.skip_type_hints:
            if (
                not parsed_node.value
                and self._within_class
                and not self._within_function
            ):
                parsed_node.annotation = ast.Name("int")
            elif parsed_node.value is None:
                return None
            else:
                return ast.Assign([parsed_node.target], parsed_node.value)

        return parsed_node

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST | None:
        if get_node_name(node.target) in self.tokens_config.variables_to_skip:
            return None

        return self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> ast.AST | None:
        """Removes imports provided in config, deleting the whole
        node if no imports are left"""
        node.names = [
            alias
            for alias in node.names
            if alias.name not in self.tokens_config.module_imports_to_skip
        ]

        if not node.names:
            return None

        return self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST | None:
        normalized_module_name: str = node.module or ""
        if normalized_module_name in self.tokens_config.module_imports_to_skip:
            return None

        node.names = [
            alias
            for alias in node.names
            if alias.name not in self.tokens_config.from_imports_to_skip
            and alias.name not in self.optimizations_config.vars_to_fold
            and alias.name not in self.optimizations_config.enums_to_fold
        ]

        if node.module == "__future__" and self._skippable_futures:
            node.names = [
                alias
                for alias in node.names
                if alias.name not in self._skippable_futures
            ]

        if not node.names:
            return None

        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        """Extends super's implementation by adding constant folding"""
        if node.id in self.optimizations_config.vars_to_fold:
            constant_value = self.optimizations_config.vars_to_fold[node.id]
            return ast.Constant(constant_value)
        else:
            return self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> ast.AST:
        if self.tokens_config.dict_keys_to_skip:
            new_dict = {
                k: v
                for k, v in zip(node.keys, node.values)
                if getattr(k, "value", "") not in self.tokens_config.dict_keys_to_skip
            }
            node.keys = list(new_dict.keys())
            node.values = list(new_dict.values())

        return self.generic_visit(node)

    def visit_If(self, node: ast.If) -> ast.AST | list[ast.stmt] | None:
        parsed_node: ast.AST = self.generic_visit(node)

        if isinstance(parsed_node, ast.If) and isinstance(
            parsed_node.test, ast.Constant
        ):
            if_body: list[ast.stmt] = (
                parsed_node.body if parsed_node.test.value else parsed_node.orelse
            )
            return if_body or None

        return parsed_node

    def visit_IfExp(self, node: ast.IfExp) -> ast.AST | None:
        parsed_node = self.generic_visit(node)

        if isinstance(parsed_node, ast.IfExp) and isinstance(
            parsed_node.test, ast.Constant
        ):
            return parsed_node.body if parsed_node.test.value else parsed_node.orelse

        return parsed_node

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if is_return_none(node):
            node.value = None

        return self.generic_visit(node)

    def visit_Pass(self, node: ast.Pass) -> None:
        """Always returns None. Caller responsible for ensuring empty bodies
        are populated with a Pass node."""
        return None  # This could be toggleable

    def visit_Call(self, node: ast.Call) -> ast.AST | None:
        if (
            self.optimizations_config.assume_this_machine
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            function_call_key: str = f"{node.func.value.id}.{node.func.attr}"

            if function_call_key in machine_dependent_functions:
                return ast.Constant(machine_dependent_functions[function_call_key])

        return self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        if (
            isinstance(node.value, ast.Call)
            and get_node_name(node.value.func) in self.tokens_config.functions_to_skip
        ):
            return None

        return self.generic_visit(node)

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
                return ast.Constant(~parsed_node.operand.value)  # type: ignore
            if isinstance(parsed_node.op, ast.UAdd):
                return parsed_node.operand

        return parsed_node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        # Need to visit first since a BinOp might contain a Binop
        # and constants need to be folded depth first
        parsed_node: ast.AST = self.generic_visit(node)

        if (
            self.optimizations_config.fold_constants
            and isinstance(parsed_node, ast.BinOp)
            and isinstance(parsed_node.left, ast.Constant)
            and isinstance(parsed_node.right, ast.Constant)
        ):
            return self._ast_constants_operation(
                parsed_node.left, parsed_node.right, parsed_node.op
            )

        return parsed_node

    def visit_arg(self, node: ast.arg) -> ast.AST:
        if self.token_types_config.skip_type_hints:
            node.annotation = None
        return self.generic_visit(node)

    def visit_arguments(self, node: ast.arguments) -> ast.AST:
        if self.token_types_config.skip_type_hints:
            if node.kwarg is not None:
                node.kwarg.annotation = None
            if node.vararg is not None:
                node.vararg.annotation = None

        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        parsed_node: ast.BoolOp = self.generic_visit(node)  # type: ignore

        if isinstance(parsed_node.op, ast.Or) or isinstance(parsed_node.op, ast.And):
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

    def _is_assign_of_folded_constant(
        self, target: ast.expr, value: ast.expr | None
    ) -> bool:
        """Returns if node is assignment of a value that we are folding. In this case,
        there is no need to assign the value since its use"""

        return (
            isinstance(target, ast.Name)
            and target.id in self.optimizations_config.vars_to_fold
            and isinstance(value, ast.Constant)
        )

    def _use_version_optimization(self, min_version: tuple[int, int]) -> bool:
        return (
            False
            if self.target_python_version is None
            else self.target_python_version >= min_version
        )

    def _has_code_to_skip(self) -> bool:
        return (
            self.target_python_version is not None
            or len(self.optimizations_config.vars_to_fold) > 0
            or self.optimizations_config.has_code_to_skip()
            or self.tokens_config.has_code_to_skip()
            or self.token_types_config.has_code_to_skip()
        )

    def _should_skip_function_assign(self, node: ast.Assign | ast.AnnAssign) -> bool:
        return (
            isinstance(node.value, ast.Call)
            and get_node_name(node.value.func) in self.tokens_config.functions_to_skip
        )

    def _warn_unused_skips(self):
        for (
            token_type,
            not_found_tokens,
        ) in self.tokens_config.get_missing_tokens_iter():
            warnings.warn(
                f"{self.module_name}: requested to skip {token_type} "
                f"{not_found_tokens} but was not found"
            )

    @staticmethod
    def _ast_constants_operation(
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
                result = left_value + right_value  # type: ignore
            case ast.Sub():
                result = left_value - right_value  # type: ignore
            case ast.Mult():
                result = left_value * right_value  # type: ignore
            case ast.Div():
                result = left_value / right_value  # type: ignore
            case ast.FloorDiv():
                result = left_value // right_value  # type: ignore
            case ast.Mod():
                result = left_value % right_value  # type: ignore
            case ast.Pow():
                result = left_value**right_value  # type: ignore
            case ast.LShift():
                result = left_value << right_value  # type: ignore
            case ast.RShift():
                result = left_value >> right_value  # type: ignore
            case ast.BitOr():
                result = left_value | right_value  # type: ignore
            case ast.BitXor():
                result = left_value ^ right_value  # type: ignore
            case ast.BitAnd():
                result = left_value & right_value  # type: ignore
            case ast.Eq():
                result = left_value == right_value
            case ast.NotEq():
                result = left_value != right_value
            case ast.Lt():
                result = left_value < right_value  # type: ignore
            case ast.LtE():
                result = left_value <= right_value  # type: ignore
            case ast.Gt():
                result = left_value > right_value  # type: ignore
            case ast.GtE():
                result = left_value >= right_value  # type: ignore
            case _:
                raise ValueError(f"Invalid operation: {operation.__class__.__name__}")

        return ast.Constant(result)
