import pytest

from personal_python_ast_optimizer.config import (
    TokenTypesToSkipConfig,
    TypeHintsToSkip,
)
from tests.utils import optimize_and_assert_correctness

_TYPE_HINT_EXAMPLE: str = """
import some_type

a: some_type

def b() -> None:
    c: int = 3
    print(c)

class C:
    a: str
"""

_GENERICS_EXAMPLE: str = """
def a[FOO, BAR](a: FOO, b: BAR) -> None:
    print(a, b)
class A[FOO]:
    def __init__(self,a:FOO):
        self.a:FOO=a
"""


def test_remove_no_type_hints():
    expected: str = """import some_type
a:some_type
def b()->None:c:int=3;print(c)
class C:a:str"""
    optimize_and_assert_correctness(
        _TYPE_HINT_EXAMPLE,
        expected,
        token_types_to_skip=TokenTypesToSkipConfig(
            skip_type_hints=TypeHintsToSkip.NONE
        ),
    )


def test_removes_type_hints_all_but_class_var():
    expected: str = "def b():c=3;print(c)\nclass C:a:str"
    optimize_and_assert_correctness(_TYPE_HINT_EXAMPLE, expected)


def test_remove_all_type_hints():
    expected: str = "def b():c=3;print(c)\nclass C:pass"

    optimize_and_assert_correctness(
        _TYPE_HINT_EXAMPLE,
        expected,
        token_types_to_skip=TokenTypesToSkipConfig(skip_type_hints=TypeHintsToSkip.ALL),
    )


def test_generics_keep():
    expected: str = """def a[FOO,BAR](a,b):print(a,b)
class A[FOO]:\n\tdef __init__(self,a):self.a=a"""

    optimize_and_assert_correctness(_GENERICS_EXAMPLE, expected)


@pytest.mark.parametrize(
    "skip_type_hints", [TypeHintsToSkip.ALL, TypeHintsToSkip.ALL_BUT_CLASS_VARS]
)
def test_generics_remove(skip_type_hints: TypeHintsToSkip):
    expected: str = """def a(a,b):print(a,b)
class A:\n\tdef __init__(self,a):self.a=a"""

    optimize_and_assert_correctness(
        _GENERICS_EXAMPLE,
        expected,
        token_types_to_skip=TokenTypesToSkipConfig(
            skip_type_hints=skip_type_hints, skip_generics=True
        ),
    )
