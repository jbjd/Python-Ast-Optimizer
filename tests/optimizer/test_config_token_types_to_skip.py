import pytest

from personal_python_ast_optimizer.config import (
    CodeToSkipConfig,
    TokensToSkip,
    TokensToSkipConfig,
    TokenTypesToSkipConfig,
    TypeHintsToSkip,
)
from tests.utils import optimize_and_assert_correctness


def test_exclude_classes():
    """Should remove class definitions and use as base class."""

    source: str = """
class A(ABC):
    pass

class B:
    pass
"""
    expected: str = "class A:pass"
    optimize_and_assert_correctness(
        source,
        expected,
        tokens_to_skip=TokensToSkipConfig(classes_to_skip=TokensToSkip({"ABC", "B"})),
    )


def test_exclude_decorators():
    """Should remove decorators from functions and classes."""

    source: str = """
@some_dec
class A:
    pass

@abc.abc
@abc.abc.abc
def B():
    pass
"""
    expected: str = "class A:pass\n@abc.abc.abc\ndef B():pass"
    optimize_and_assert_correctness(
        source,
        expected,
        tokens_to_skip=TokensToSkipConfig(
            decorators_to_skip=TokensToSkip({"some_dec", "abc.abc"})
        ),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
a = 1
foo: int = 2
""",
            "a=1",
        ),
        (
            """
def bar():
    foo = 2
""",
            "def bar():pass",
        ),
        (
            """
def bar():
    test = 1
    foo = 2
""",
            "def bar():test=1",
        ),
        (
            """
def bar():
    foo = some_func()
    test = 1
""",
            "def bar():test=1",
        ),
        (
            """
def bar():
    bar.foo = 2
    test = 1
""",
            "def bar():test=1",
        ),
        (
            "*foo=(1,2)",
            "*foo=(1,2)",
        ),
    ],
)
def test_exclude_assign(source: str, expected: str):
    """Should remove assignments when applicable."""

    optimize_and_assert_correctness(
        source,
        expected,
        tokens_to_skip=TokensToSkipConfig(
            assignments_to_skip=TokensToSkip({"foo", "bar.foo"})
        ),
        token_types_to_skip=TokenTypesToSkipConfig(
            skip_type_hints=TypeHintsToSkip.NONE
        ),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
def bar():
    def foo():
        pass
""",
            "def bar():pass",
        ),
        (
            "logger.debug();foo()",
            "logger.debug()",
        ),
        (
            """
def foo():
    print(0)

    foo()
""",
            "",
        ),
        ("logger.warn()", ""),
    ],
)
def test_exclude_function_def(source: str, expected: str):
    """Should remove function definitions and calls."""

    optimize_and_assert_correctness(
        source,
        expected,
        tokens_to_skip=TokensToSkipConfig(
            functions_to_skip=TokensToSkip({"foo", "logger.warn"})
        ),
    )


def test_exclude_from_imports():
    """Should remove from imports."""

    source: str = """
from . import asdf
from .a import foo
from a.b import bar2
from ..a import abcd
"""
    expected: str = "from ..a import abcd"

    optimize_and_assert_correctness(
        source,
        expected,
        tokens_to_skip=TokensToSkipConfig(
            from_imports_to_skip=TokensToSkip(
                [(".", "asdf"), (".a", "foo"), ("a.b", "bar2")]
            )
        ),
        code_to_skip=CodeToSkipConfig(skip_unused_imports=False),
    )


def test_exclude_module_imports():
    """Should remove module imports."""

    source: str = """
import numpy
import a
import a as b
import a as c
"""
    expected: str = "import a as c"

    optimize_and_assert_correctness(
        source,
        expected,
        tokens_to_skip=TokensToSkipConfig(
            module_imports_to_skip=TokensToSkip({"numpy", "a", "b"})
        ),
        code_to_skip=CodeToSkipConfig(skip_unused_imports=False),
    )
