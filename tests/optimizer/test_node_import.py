from personal_python_ast_optimizer.config import CodeToSkipConfig
from tests.utils import optimize_and_assert_correctness


def test_combined_imports():
    """Should combine imports where applicable."""
    source: str = """
import test
import test2
def i():
    from .b import f
    from b import c
    from b import d as e
    print()
    from b import abc
"""
    expected: str = """import test,test2
def i():from .b import f;from b import c,d as e;print();from b import abc"""

    optimize_and_assert_correctness(
        source,
        expected,
        code_to_skip=CodeToSkipConfig(skip_unused_imports=False),
    )
