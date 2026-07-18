from personal_python_ast_optimizer.config import CodeToSkipConfig
from tests.utils import optimize_and_assert_correctness

_EXAMPLE_TYPING_CAST: str = """
from typing import cast

a = cast(str, 1)
"""


def test_skip_typing_cast():
    """Should remove all cast calls and replace with second arg."""

    expected: str = "a=1"

    optimize_and_assert_correctness(
        _EXAMPLE_TYPING_CAST,
        expected,
        code_to_skip=CodeToSkipConfig(skip_typing_cast=True),
    )


def test_no_skip_typing_cast():
    """Should remove no cast calls."""

    expected: str = "from typing import cast\na=cast(str,1)"

    optimize_and_assert_correctness(
        _EXAMPLE_TYPING_CAST,
        expected,
        code_to_skip=CodeToSkipConfig(skip_typing_cast=False),
    )
