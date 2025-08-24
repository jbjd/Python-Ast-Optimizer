from abc import ABC, abstractmethod
from typing import Iterator


class TokensToSkip(dict[str, int]):

    __slots__ = ("token_type",)

    def __init__(self, tokens_to_skip: set[str] | None, token_type: str) -> None:
        tokens_and_counts: dict[str, int] = self._set_to_dict_of_counts(tokens_to_skip)
        super().__init__(tokens_and_counts)

        self.token_type: str = token_type

    def __contains__(self, key: str) -> bool:  # type: ignore
        """Returns if token is marked to skip and
        increments internal counter when True is returned"""
        contains: bool = super().__contains__(key)

        if contains:
            self[key] += 1

        return contains

    def get_not_found_tokens(self) -> set[str]:
        return set(token for token, found_count in self.items() if found_count == 0)

    @staticmethod
    def _set_to_dict_of_counts(input_set: set[str] | None) -> dict[str, int]:
        if not input_set:
            return {}

        return {key: 0 for key in input_set}


class Config(ABC):

    __slots__ = ()

    @abstractmethod
    def __init__(self) -> None:
        pass

    def has_code_to_skip(self) -> bool:
        return any(getattr(self, attr) for attr in self.__slots__)  # type: ignore


class TokensConfig(Config):

    __slots__ = (
        "_no_warn",
        "from_imports_to_skip",
        "functions_to_skip",
        "variables_to_skip",
        "classes_to_skip",
        "dict_keys_to_skip",
        "decorators_to_skip",
        "module_imports_to_skip",
    )

    def __init__(
        self,
        from_imports_to_skip: set[str] | None = None,
        functions_to_skip: set[str] | None = None,
        variables_to_skip: set[str] | None = None,
        classes_to_skip: set[str] | None = None,
        dict_keys_to_skip: set[str] | None = None,
        decorators_to_skip: set[str] | None = None,
        module_imports_to_skip: set[str] | None = None,
        no_warn: set[str] | None = None,
    ):
        self.from_imports_to_skip = TokensToSkip(from_imports_to_skip, "from imports")
        self.functions_to_skip = TokensToSkip(functions_to_skip, "functions")
        self.variables_to_skip = TokensToSkip(variables_to_skip, "variables")
        self.classes_to_skip = TokensToSkip(classes_to_skip, "classes")
        self.dict_keys_to_skip = TokensToSkip(dict_keys_to_skip, "dict keys")
        self.decorators_to_skip = TokensToSkip(decorators_to_skip, "decorators")
        self.module_imports_to_skip = TokensToSkip(
            module_imports_to_skip, "module imports"
        )
        self._no_warn: set[str] = no_warn if no_warn is not None else set()

    def __iter__(self) -> Iterator[TokensToSkip]:
        for attr in self.__slots__:
            if attr != "_no_warn":
                yield getattr(self, attr)

    def has_code_to_skip(self) -> bool:
        return any(self)  # type: ignore

    def get_missing_tokens_iter(self) -> Iterator[tuple[str, str]]:
        for tokens_to_skip in self:
            not_found_tokens: list[str] = [
                t
                for t in tokens_to_skip.get_not_found_tokens()
                if t not in self._no_warn
            ]
            if not_found_tokens:
                yield (tokens_to_skip.token_type, ",".join(not_found_tokens))


class SectionsConfig(Config):
    __slots__ = ("skip_name_equals_main",)

    def __init__(self, skip_name_equals_main: bool = False) -> None:
        self.skip_name_equals_main: bool = skip_name_equals_main


class ExtrasConfig(Config):
    __slots__ = (
        "fold_constants",
        "skip_dangling_expressions",
        "skip_type_hints",
        "skip_overload_functions",
        "warn_unusual_code",
    )

    def __init__(
        self,
        warn_unusual_code: bool = True,
        fold_constants: bool = True,
        skip_dangling_expressions: bool = True,
        skip_type_hints: bool = True,
        skip_overload_functions: bool = False,
    ) -> None:
        self.fold_constants: bool = fold_constants
        self.skip_dangling_expressions: bool = skip_dangling_expressions
        self.skip_type_hints: bool = skip_type_hints
        self.skip_overload_functions: bool = skip_overload_functions
        self.warn_unusual_code: bool = warn_unusual_code


class SkipConfig(Config):

    __slots__ = (
        "module_name",
        "target_python_version",
        "vars_to_fold",
        "sections_config",
        "tokens_config",
        "extras_config",
    )

    def __init__(
        self,
        module_name: str = "",
        target_python_version: tuple[int, int] | None = None,
        vars_to_fold: dict[str, int | str] | None = None,
        sections_config: SectionsConfig = SectionsConfig(),
        tokens_config: TokensConfig = TokensConfig(),
        extras_config: ExtrasConfig = ExtrasConfig(),
    ) -> None:
        self.module_name: str = module_name
        self.target_python_version: tuple[int, int] | None = target_python_version
        self.vars_to_fold: dict[str, int | str] = (
            {} if vars_to_fold is None else vars_to_fold
        )
        self.sections_config: SectionsConfig = sections_config
        self.tokens_config: TokensConfig = tokens_config
        self.extras_config: ExtrasConfig = extras_config

    def has_code_to_skip(self) -> bool:
        return (
            self.target_python_version is not None
            or len(self.vars_to_fold) > 0
            or self.sections_config.has_code_to_skip()
            or self.tokens_config.has_code_to_skip()
            or self.extras_config.has_code_to_skip()
        )
