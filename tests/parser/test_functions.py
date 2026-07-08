from personal_python_ast_optimizer.config import CodeToSkipConfig
from tests.utils import BeforeAndAfter, optimize_and_assert_correctness


def test_function_dangling_constants():
    before_and_after = BeforeAndAfter(
        """
def foo(bar: str) -> None:
    '''Some Doc String'''

    3  # This is some dangling constant
    a: int
    return
""",
        "def foo(bar):pass",
    )
    optimize_and_assert_correctness(before_and_after)


def test_function_with_many_args():
    before_and_after = BeforeAndAfter(
        """
def foo(bar, spam, eggs):
    a: int = 1
    return a
""",
        "def foo(bar,spam,eggs):a=1;return a",
    )
    optimize_and_assert_correctness(before_and_after)


def test_function_with_many_returns():
    before_and_after = BeforeAndAfter(
        """
def foo(bar):
    if bar:
        return None
    return 1
""",
        """
def foo(bar):
\tif bar:return
\treturn 1
""".strip(),
    )
    optimize_and_assert_correctness(before_and_after)


def test_function_overload():
    before_and_after = BeforeAndAfter(
        """
@overload
def test_overload(a: None) -> None: ...

@overload
def test_overload(a: int) -> int: ...

def test_overload(a: float) -> int: do_something()
""",
        "def test_overload(a):do_something()",
    )
    optimize_and_assert_correctness(
        before_and_after,
        code_to_skip_config=CodeToSkipConfig(skip_overload_functions=True),
    )


def test_typing_cast_remove():
    before_and_after = BeforeAndAfter(
        """
from typing import cast

a = cast(str, 1)
""",
        "a=1",
    )
    optimize_and_assert_correctness(
        before_and_after,
        code_to_skip_config=CodeToSkipConfig(skip_typing_cast=True),
    )


def test_typing_cast():
    before_and_after = BeforeAndAfter(
        """
from typing import cast

a = cast(str, 1)
""",
        "from typing import cast\na=cast(str,1)",
    )
    optimize_and_assert_correctness(
        before_and_after,
        code_to_skip_config=CodeToSkipConfig(skip_typing_cast=False),
    )
