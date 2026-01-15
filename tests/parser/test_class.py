from personal_python_ast_optimizer.parser.config import (
    TokenTypesConfig,
    TypeHintsToSkip,
)
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_class_only_docstring():
    before_and_after = BeforeAndAfter(
        """
class Foo():
    '''Some Class'''
""",
        "class Foo:pass",
    )
    run_minifier_and_assert_correct(before_and_after)


def test_class_preserves_type_hints():
    before_and_after = BeforeAndAfter(
        """
class SomeTuple():
    '''A tuple, wow!'''
    thing1: str
    thing2: int

    def a():
        class B:
            thing3: None
        return B""",
        """class SomeTuple:
\tthing1:int;thing2:int
\tdef a():
\t\tclass B:thing3:int
\t\treturn B""",
    )
    run_minifier_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(
            skip_type_hints=TypeHintsToSkip.ALL_BUT_CLASS_VARS
        ),
    )


def test_class_skip_type_hints():
    before_and_after = BeforeAndAfter(
        """
class SomeTuple():
    '''A tuple, wow!'''
    thing1: str
    thing2: int

    def a():
        class B:
            thing3: None
        return B""",
        """class SomeTuple:
\tdef a():
\t\tclass B:pass
\t\treturn B""",
    )
    run_minifier_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(skip_type_hints=TypeHintsToSkip.ALL),
    )
