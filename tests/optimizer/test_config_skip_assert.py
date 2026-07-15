from personal_python_ast_optimizer.config import TokenTypesToSkipConfig
from tests.utils import optimize_and_assert_correctness

_ASSERT_EXAMPLE: str = "def foo1(val):assert val;val()"


def test_skip_assert():
    optimize_and_assert_correctness(
        _ASSERT_EXAMPLE,
        "def foo1(val):val()",
        token_types_to_skip=TokenTypesToSkipConfig(skip_asserts=True),
    )


def test_no_skip_assert():
    optimize_and_assert_correctness(
        _ASSERT_EXAMPLE,
        _ASSERT_EXAMPLE,
        token_types_to_skip=TokenTypesToSkipConfig(skip_asserts=False),
    )
