from personal_python_ast_optimizer.parser.config import (
    TokenTypesConfig,
    TypeHintsToSkip,
)
from tests.utils import BeforeAndAfter, optimize_and_assert_correct

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

    optimize_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(skip_type_hints=TypeHintsToSkip.NONE),
    )


def test_removes_type_hints_all_but_class_var():
    before_and_after = BeforeAndAfter(
        _TYPE_HINT_EXAMPLE,
        "def b():c=3;print(c)\nclass C:a:str",
    )

    optimize_and_assert_correct(before_and_after)


def test_remove_all_type_hints():
    before_and_after = BeforeAndAfter(
        _TYPE_HINT_EXAMPLE,
        "def b():c=3;print(c)\nclass C:pass",
    )

    optimize_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(skip_type_hints=TypeHintsToSkip.ALL),
    )
