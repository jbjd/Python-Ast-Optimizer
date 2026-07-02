import pytest

from personal_python_ast_optimizer.config import (
    CodeToSkipConfig,
    ExtraOptimizationsConfig,
    TokenTypesToSkipConfig,
    TypeHintsToSkip,
)


def test_generics_without_type_hints():
    with pytest.raises(
        ValueError, match=r"Can't skip Generics if not skipping type hints"
    ):
        TokenTypesToSkipConfig(skip_generics=True, skip_type_hints=TypeHintsToSkip.NONE)


def test_perserve_imports_without_skip_unused_imports():
    with pytest.raises(
        ValueError, match=r"Can't preserve imports if skip_unused_imports is False"
    ):
        CodeToSkipConfig(skip_unused_imports=False, unused_imports_to_preserve=["foo"])


def test_target_python_invalid():
    with pytest.raises(ValueError, match=r"Target Python version must be at least 3.0"):
        ExtraOptimizationsConfig(target_python_version=(2, 7))
