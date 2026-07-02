import pytest

from personal_python_ast_optimizer.parser.config import (
    TokenTypesConfig,
    TypeHintsToSkip,
)
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_TYPE_HINT_EXAMPLE: str = """
import some_type

a: some_type

def b() -> None:
    c: int = 3
    print(c)

class C:
    a: str
"""


def test_remove_no_type_hints():
    before_and_after = BeforeAndAfter(
        _TYPE_HINT_EXAMPLE,
        """import some_type
a:some_type
def b()->None:c:int=3;print(c)
class C:a:str""",
    )

    run_minifier_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(skip_type_hints=TypeHintsToSkip.NONE),
    )


def test_removes_type_hints_all_but_class_var():
    before_and_after = BeforeAndAfter(
        _TYPE_HINT_EXAMPLE,
        "def b():c=3;print(c)\nclass C:a:str",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_remove_all_type_hints():
    before_and_after = BeforeAndAfter(
        _TYPE_HINT_EXAMPLE,
        "def b():c=3;print(c)\nclass C:pass",
    )

    run_minifier_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(skip_type_hints=TypeHintsToSkip.ALL),
    )


def test_generics_config():
    with pytest.raises(
        ValueError, match="Can't skip Generics if not skipping type hints"
    ):
        TokenTypesConfig(skip_type_hints=TypeHintsToSkip.NONE, skip_generics=True)


def test_generics_keep():
    before_and_after = BeforeAndAfter(
        """
def a[FOO, BAR](a: FOO, b: BAR) -> None:
    print(a, b)
class A[FOO]:
    def __init__(self,a:FOO):
        self.a:FOO=a
""",
        """def a[FOO,BAR](a,b):print(a,b)
class A[FOO]:\n\tdef __init__(self,a):self.a=a""",
    )

    run_minifier_and_assert_correct(before_and_after)


@pytest.mark.parametrize(
    "skip_type_hints", [TypeHintsToSkip.ALL, TypeHintsToSkip.ALL_BUT_CLASS_VARS]
)
def test_generics_remove(skip_type_hints: TypeHintsToSkip):
    before_and_after = BeforeAndAfter(
        """
def a[FOO, BAR](a: FOO, b: BAR) -> None:
    print(a, b)
class A[FOO]:
    def __init__(self,a:FOO):
        self.a:FOO=a
""",
        """def a(a,b):print(a,b)
class A:\n\tdef __init__(self,a):self.a=a""",
    )

    run_minifier_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(
            skip_type_hints=skip_type_hints, skip_generics=True
        ),
    )
