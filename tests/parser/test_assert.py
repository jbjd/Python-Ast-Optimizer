from personal_python_ast_optimizer.parser.config import TokenTypesConfig
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_assert_same_line():
    before_and_after = BeforeAndAfter(
        """
def test_foo():
    assert 1
    assert 2, "bar"
    assert 3
""",
        "def test_foo():assert 1;assert 2,'bar';assert 3",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_skip_assert():
    before_and_after = BeforeAndAfter(
        """
while 1:
    assert val
    foo()
""",
        "while 1:foo()",
    )

    run_minifier_and_assert_correct(
        before_and_after, token_types_config=TokenTypesConfig(skip_asserts=True)
    )
