import ast
import warnings

from personal_python_ast_optimizer.futures import get_unneeded_futures
from personal_python_ast_optimizer.parser.config import (
    ExtrasConfig,
    SectionsConfig,
    SkipConfig,
    TokensConfig,
)
from personal_python_ast_optimizer.parser.utils import (
    can_skip_annotation_assign,
    first_occurrence_of_type,
    get_node_name,
    is_name_equals_main_node,
    is_return_none,
    skip_base_classes,
    skip_dangling_expressions,
    skip_decorators,
)


class AstNodeSkipper(ast.NodeTransformer):

    __slots__ = (
        "_within_class",
        "_within_function",
        "module_name",
        "vars_to_fold",
        "target_python_version",
        "extras_config",
        "sections_config",
        "tokens_config",
    )

    def __init__(self, config: SkipConfig) -> None:
        self.module_name: str = config.module_name
        self.vars_to_fold: dict[str, int | str] = config.vars_to_fold
        self.target_python_version: tuple[int, int] | None = (
            config.target_python_version
        )
        self.extras_config: ExtrasConfig = config.extras_config
        self.sections_config: SectionsConfig = config.sections_config
        self.tokens_config: TokensConfig = config.tokens_config

        self._within_class: bool = False
        self._within_function: bool = False

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

    def generic_visit(self, node: ast.AST) -> ast.AST:
        node_to_return: ast.AST = super().generic_visit(node)

        if not isinstance(node, ast.Module) and hasattr(node, "body") and not node.body:
            node.body.append(ast.Pass())

        return node_to_return

    def visit_Module(self, node: ast.Module) -> ast.AST:
        if not self._has_code_to_skip():
            return node

        if self.extras_config.skip_dangling_expressions:
            skip_dangling_expressions(node)

        try:
            return self.generic_visit(node)
        finally:
            self._warn_unused_skips()

    @_within_class_node
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST | None:
        if node.name in self.tokens_config.classes_to_skip:
            return None

        if self._use_version_optimization((3, 0)):
            skip_base_classes(node, ["object"])

        if self.extras_config.skip_dangling_expressions:
            skip_dangling_expressions(node)
        skip_base_classes(node, self.tokens_config.classes_to_skip)
        skip_decorators(node, self.tokens_config.decorators_to_skip)

        return self.generic_visit(node)

    @_within_function_node
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        if node.name in self.tokens_config.functions_to_skip:
            return None

        self._handle_function_node(node)

        return self.generic_visit(node)

    @_within_function_node
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST | None:
        if node.name in self.tokens_config.functions_to_skip:
            return None

        self._handle_function_node(node)

        return self.generic_visit(node)

    def _handle_function_node(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Handles skips for both async/regular functions"""
        if self.extras_config.skip_type_hints:
            node.returns = None

        if self.extras_config.skip_dangling_expressions:
            skip_dangling_expressions(node)

        skip_decorators(node, self.tokens_config.decorators_to_skip)

        last_body_node: ast.stmt = node.body[-1]
        if isinstance(last_body_node, ast.Return) and (
            is_return_none(last_body_node) or last_body_node.value is None
        ):
            node.body = node.body[:-1]

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
        if len(new_targets) == 0:
            return None

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

            if len(node.targets[0].elts) == 0:
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
            or (
                self.extras_config.skip_type_hints
                and can_skip_annotation_assign(
                    node, self._within_class, self._within_function
                )
            )
        ):
            return None

        parsed_node: ast.AnnAssign = self.generic_visit(node)  # type: ignore

        if self.extras_config.skip_type_hints:
            if (
                not parsed_node.value
                and self._within_class
                and not self._within_function
            ):
                parsed_node.annotation = ast.Constant("Any")
            elif parsed_node.value is None:
                # This should be unreachable
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
        ]

        if node.module == "__future__" and self.target_python_version is not None:
            skippable_futures: list[str] = get_unneeded_futures(
                self.target_python_version
            )
            if self.extras_config.skip_type_hints:
                skippable_futures.append("annotations")

            node.names = [
                alias for alias in node.names if alias.name not in skippable_futures
            ]

        if self.vars_to_fold:
            node.names = [
                alias for alias in node.names if alias.name not in self.vars_to_fold
            ]

        if not node.names:
            return None

        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        """Extends super's implementation by adding constant folding"""
        if node.id in self.vars_to_fold:
            constant_value = self.vars_to_fold[node.id]
            return ast.Constant(constant_value)
        else:
            return self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> ast.AST:
        new_dict = {
            k: v
            for k, v in zip(node.keys, node.values)
            if getattr(k, "value", "") not in self.tokens_config.dict_keys_to_skip
        }
        node.keys = list(new_dict.keys())
        node.values = list(new_dict.values())

        return self.generic_visit(node)

    def visit_If(self, node: ast.If) -> ast.AST | None:
        if self.sections_config.skip_name_equals_main and is_name_equals_main_node(
            node.test
        ):
            return None

        return self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if is_return_none(node):
            node.value = None

        return self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        if (
            isinstance(node.value, ast.Call)
            and get_node_name(node.value.func) in self.tokens_config.functions_to_skip
        ):
            return None

        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        # Need to visit first since a BinOp might contain a Binop
        # and constants need to be folded depth first
        parsed_node: ast.AST = self.generic_visit(node)

        if (
            self.extras_config.fold_constants
            and isinstance(parsed_node, ast.BinOp)
            and isinstance(parsed_node.left, ast.Constant)
            and isinstance(parsed_node.right, ast.Constant)
        ):
            left = parsed_node.left.value
            right = parsed_node.right.value
            match parsed_node.op.__class__.__name__:
                case "Add":
                    return ast.Constant(left + right)
                case "Sub":
                    return ast.Constant(left - right)
                case "Mult":
                    return ast.Constant(left * right)
                case "Div":
                    return ast.Constant(left / right)
                case "FloorDiv":
                    return ast.Constant(left // right)
                case "Mod":
                    return ast.Constant(left % right)
                case "Pow":
                    return ast.Constant(left**right)
                case "LShift":
                    return ast.Constant(left << right)
                case "RShift":
                    return ast.Constant(left >> right)
                case "BitOr":
                    return ast.Constant(left | right)
                case "BitXor":
                    return ast.Constant(left ^ right)
                case "BitAnd":
                    return ast.Constant(left & right)

        return parsed_node

    def visit_arg(self, node: ast.arg) -> ast.AST:
        if self.extras_config.skip_type_hints:
            node.annotation = None
        return self.generic_visit(node)

    def visit_arguments(self, node: ast.arguments) -> ast.AST:
        if self.extras_config.skip_type_hints:
            if node.kwarg is not None:
                node.kwarg.annotation = None
            if node.vararg is not None:
                node.vararg.annotation = None

        return self.generic_visit(node)

    def _is_assign_of_folded_constant(
        self, target: ast.expr, value: ast.expr | None
    ) -> bool:
        """Returns if node is assignment of a value that we are folding. In this case,
        there is no need to assign the value since its use"""

        return (
            isinstance(target, ast.Name)
            and target.id in self.vars_to_fold
            and isinstance(value, ast.Constant)
        )

    def _use_version_optimization(self, min_version: tuple[int, int]) -> bool:
        if self.target_python_version is None:
            return False

        return self.target_python_version >= min_version

    def _has_code_to_skip(self) -> bool:
        return (
            self.target_python_version is not None
            or len(self.vars_to_fold) > 0
            or self.extras_config.has_code_to_skip()
            or self.tokens_config.has_code_to_skip()
            or self.sections_config.has_code_to_skip()
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
