from personal_python_ast_optimizer.config import CodeToSkipConfig
from tests.utils import optimize_and_assert_correctness


def test_skip_overload_functions():
    """Should skip unneeded overload functions."""

    source: str = """
@overload
def test_overload(a: None) -> None: ...

@overload
def test_overload(a: int) -> int: ...

def test_overload(a: float) -> int: do_something()
"""
    expected: str = "def test_overload(a):do_something()"

    optimize_and_assert_correctness(
        source,
        expected,
        code_to_skip=CodeToSkipConfig(skip_overload_functions=True),
    )
