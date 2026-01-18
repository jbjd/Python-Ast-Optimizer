from personal_python_ast_optimizer.parser.config import (
    TokenTypesConfig,
    TypeHintsToSkip,
)
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_removes_type_hints_all_but_class_var():
    before_and_after = BeforeAndAfter(
        """
import some_type

a: some_type

def b():
    c: int = 3
    print(c)

class C:
    a: str
""",
        "def b():c=3;print(c)\nclass C:a:str",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_remove_no_type_hints():
    before_and_after = BeforeAndAfter(
        """
import some_type

a: some_type

def b():
    c: int = 3
    print(c)

class C:
    a: str
""",
        """import some_type
a:some_type
def b():c:int=3;print(c)
class C:a:str""",
    )

    run_minifier_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(skip_type_hints=TypeHintsToSkip.NONE),
    )


def test_remove_all_type_hints():
    before_and_after = BeforeAndAfter(
        """
import some_type

a: some_type

def b():
    c: int = 3
    print(c)

class C:
    a: str
""",
        "def b():c=3;print(c)\nclass C:pass",
    )

    run_minifier_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(skip_type_hints=TypeHintsToSkip.ALL),
    )
