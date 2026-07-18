import pytest

from personal_python_ast_optimizer.config import (
    CodeToSkipConfig,
    TokenTypesToSkipConfig,
)


def test_generics_without_type_hints():
    with pytest.raises(
        ValueError, match=r"Can't skip Generics unless all type hints are skipped"
    ):
        TokenTypesToSkipConfig(skip_generics_and_alias=True)


def test_perserve_imports_without_skip_unused_imports():
    with pytest.raises(
        ValueError, match=r"Can't preserve imports if skip_unused_imports is False"
    ):
        CodeToSkipConfig(skip_unused_imports=False, unused_imports_to_preserve=["foo"])
