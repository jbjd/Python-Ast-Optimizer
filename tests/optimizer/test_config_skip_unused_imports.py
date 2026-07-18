import pytest

from personal_python_ast_optimizer.config import CodeToSkipConfig
from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
if a == b:
    import foo
    import bar

print(bar)""",
            "if a==b:import bar\nprint(bar)",
        ),
        (
            """
import foo

a: foo = bar()

def asdf(a: foo) -> foo:
    return a""",
            "a=bar()\ndef asdf(a):return a",
        ),
        (
            """
from .typing import foo

a: foo | None = bar()

def asdf(a: foo) -> foo:
    return a""",
            "a=bar()\ndef asdf(a):return a",
        ),
        (
            """
from foo import bar as bar2

if False:
    bar2()

bar()""",
            "bar()",
        ),
        (
            "import asdf",
            "import asdf",
        ),
    ],
)
def test_remove_unused_import(source: str, expected: str):
    optimize_and_assert_correctness(
        source,
        expected,
        code_to_skip=CodeToSkipConfig(unused_imports_to_preserve=["asdf"]),
    )
