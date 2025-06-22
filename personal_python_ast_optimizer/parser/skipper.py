import ast
import warnings

from personal_python_ast_optimizer.futures import get_unneeded_futures
from personal_python_ast_optimizer.parser.config import (
    ExtrasToSkipConfig,
    SectionsToSkipConfig,
    SkipConfig,
    TokensToSkipConfig,
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
        "constant_vars_to_fold",
        "target_python_version",
        "extras_to_skip_config",
        "sections_to_skip_config",
        "tokens_to_skip_config",
    )

    def __init__(self, config: SkipConfig) -> None:
        self.module_name: str = config.module_name
        self.constant_vars_to_fold: dict[str, int | str] = config.constant_vars_to_fold
        self.target_python_version: tuple[int, int] | None = (
            config.target_python_version
        )
        self.extras_to_skip_config: ExtrasToSkipConfig = config.extras_to_skip_config
        self.sections_to_skip_config: SectionsToSkipConfig = (
            config.sections_to_skip_config
        )
        self.tokens_to_skip_config: TokensToSkipConfig = config.tokens_to_skip_config

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

        if self.extras_to_skip_config.skip_dangling_expressions:
            skip_dangling_expressions(node)

        try:
            return self.generic_visit(node)
        finally:
            self._warn_unused_skips()

    @_within_class_node
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST | None:
        if node.name in self.tokens_to_skip_config.classes:
            return None

        if self._use_version_optimization((3, 0)):
            skip_base_classes(node, ["object"])

        if self.extras_to_skip_config.skip_dangling_expressions:
            skip_dangling_expressions(node)
        skip_base_classes(node, self.tokens_to_skip_config.classes)
        skip_decorators(node, self.tokens_to_skip_config.decorators)

        return self.generic_visit(node)

    @_within_function_node
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
        if node.name in self.tokens_to_skip_config.functions:
            return None

        self._handle_function_node(node)

        return self.generic_visit(node)

    @_within_function_node
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST | None:
        if node.name in self.tokens_to_skip_config.functions:
            return None

        self._handle_function_node(node)

        return self.generic_visit(node)

    def _handle_function_node(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Handles skips for both async/regular functions"""
        if self.extras_to_skip_config.skip_type_hints:
            node.returns = None

        if self.extras_to_skip_config.skip_dangling_expressions:
            skip_dangling_expressions(node)

        skip_decorators(node, self.tokens_to_skip_config.decorators)

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
            var_name in self.tokens_to_skip_config.variables
            or parent_var_name in self.tokens_to_skip_config.variables
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
            or get_node_name(node.target) in self.tokens_to_skip_config.variables
            or self._is_assign_of_folded_constant(node.target, node.value)
            or (
                self.extras_to_skip_config.skip_type_hints
                and can_skip_annotation_assign(
                    node, self._within_class, self._within_function
                )
            )
        ):
            return None

        parsed_node: ast.AnnAssign = self.generic_visit(node)  # type: ignore

        if self.extras_to_skip_config.skip_type_hints:
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
        if get_node_name(node.target) in self.tokens_to_skip_config.variables:
            return None

        return self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> ast.AST | None:
        """Removes imports provided in config, deleting the whole
        node if no imports are left"""
        node.names = [
            alias
            for alias in node.names
            if alias.name not in self.tokens_to_skip_config.module_imports
        ]

        if not node.names:
            return None

        return self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST | None:
        normalized_module_name: str = node.module or ""
        if normalized_module_name in self.tokens_to_skip_config.module_imports:
            return None

        node.names = [
            alias
            for alias in node.names
            if alias.name not in self.tokens_to_skip_config.from_imports
        ]

        if node.module == "__future__" and self.target_python_version is not None:
            skippable_futures: list[str] = get_unneeded_futures(
                self.target_python_version
            )
            if self.extras_to_skip_config.skip_type_hints:
                skippable_futures.append("annotations")

            node.names = [
                alias for alias in node.names if alias.name not in skippable_futures
            ]

        if self.constant_vars_to_fold:
            node.names = [
                alias
                for alias in node.names
                if alias.name not in self.constant_vars_to_fold
            ]

        if not node.names:
            return None

        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        """Extends super's implementation by adding constant folding"""
        if node.id in self.constant_vars_to_fold:
            constant_value = self.constant_vars_to_fold[node.id]
            return ast.Constant(constant_value)
        else:
            return self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> ast.AST:
        new_dict = {
            k: v
            for k, v in zip(node.keys, node.values)
            if getattr(k, "value", "") not in self.tokens_to_skip_config.dict_keys
        }
        node.keys = list(new_dict.keys())
        node.values = list(new_dict.values())

        return self.generic_visit(node)

    def visit_If(self, node: ast.If) -> ast.AST | None:
        if is_name_equals_main_node(node.test):
            return None

        return self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if is_return_none(node):
            node.value = None

        return self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        if (
            isinstance(node.value, ast.Call)
            and get_node_name(node.value.func) in self.tokens_to_skip_config.functions
        ):
            return None

        return self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> ast.AST:
        if self.extras_to_skip_config.skip_type_hints:
            node.annotation = None
        return self.generic_visit(node)

    def visit_arguments(self, node: ast.arguments) -> ast.AST:
        if self.extras_to_skip_config.skip_type_hints:
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
            and target.id in self.constant_vars_to_fold
            and isinstance(value, ast.Constant)
        )

    def _use_version_optimization(self, min_version: tuple[int, int]) -> bool:
        if self.target_python_version is None:
            return False

        return self.target_python_version >= min_version

    def _has_code_to_skip(self) -> bool:
        return (
            self.target_python_version is not None
            or len(self.constant_vars_to_fold) > 0
            or self.extras_to_skip_config.has_code_to_skip()
            or self.tokens_to_skip_config.has_code_to_skip()
            or self.sections_to_skip_config.has_code_to_skip()
        )

    def _should_skip_function_assign(self, node: ast.Assign | ast.AnnAssign) -> bool:
        return (
            isinstance(node.value, ast.Call)
            and get_node_name(node.value.func) in self.tokens_to_skip_config.functions
        )

    def _warn_unused_skips(self):
        for tokens_to_skip in self.tokens_to_skip_config:
            not_found_tokens: list[str] = [
                t
                for t in tokens_to_skip.get_not_found_tokens()
                if t not in self.tokens_to_skip_config.no_warn
            ]
            if not_found_tokens:
                warnings.warn(
                    (
                        f"{self.module_name}: requested to skip "
                        f"{tokens_to_skip.token_type} {', '.join(not_found_tokens)}"
                        " but was not found"
                    )
                )
