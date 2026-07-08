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


def test_target_python_below_3():
    with pytest.raises(ValueError, match=r"Can't target Python version below 3.0"):
        ExtraOptimizationsConfig(target_python_version=(2, 7))


def test_target_python_above_interpreter():
    # This test might break after 10,000 years when python 99 releases
    with pytest.raises(
        ValueError, match=r"Can't target python version above current interpreter"
    ):
        ExtraOptimizationsConfig(target_python_version=(99, 0))
