import pytest

from personal_python_ast_optimizer.config import CodeToSkipConfig
from tests.utils import BeforeAndAfter, optimize_and_assert_correctness_old


def test_import_combined():
    before_and_after = BeforeAndAfter(
        """
import test
import test2
def i():
    import a
    import d
    from .b import f
    from b import c
    from b import d as e
    print()
    from b import abc
""",
        """import test,test2
def i():import a,d;from .b import f;from b import c,d as e;print();from b import abc""",
    )
    optimize_and_assert_correctness_old(
        before_and_after,
        code_to_skip=CodeToSkipConfig(skip_unused_imports=False),
    )


def test_import_star():
    before_and_after = BeforeAndAfter(
        "from ctypes import *",
        "from ctypes import*",
    )
    optimize_and_assert_correctness_old(
        before_and_after,
        code_to_skip=CodeToSkipConfig(skip_unused_imports=False),
    )


_unused_import_test_cases: list[BeforeAndAfter] = [
    BeforeAndAfter(
        """
if a == b:
    import foo
    import bar

print(a)""",
        "if a==b:pass\nprint(a)",
    ),
    BeforeAndAfter(
        """
import foo

a: foo = bar()

def asdf(a: foo) -> foo:
    return a""",
        """
a=bar()
def asdf(a):return a
""".strip(),
    ),
    BeforeAndAfter(
        """
from .typing import foo

a: foo | None = bar()

def asdf(a: foo) -> foo:
    return a""",
        """
a=bar()
def asdf(a):return a
""".strip(),
    ),
    BeforeAndAfter(
        """
from foo import bar as bar2

if False:
    bar2()

bar()
""".strip(),
        "bar()",
    ),
    BeforeAndAfter(
        "import asdf",
        "import asdf",
    ),
]


@pytest.mark.parametrize("before_and_after", _unused_import_test_cases)
def test_remove_unused_import(before_and_after: BeforeAndAfter):
    optimize_and_assert_correctness_old(
        before_and_after,
        code_to_skip=CodeToSkipConfig(unused_imports_to_preserve=["asdf"]),
    )
