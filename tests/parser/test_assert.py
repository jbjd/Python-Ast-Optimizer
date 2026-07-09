from personal_python_ast_optimizer.config import TokenTypesToSkipConfig
from tests.utils import BeforeAndAfter, optimize_and_assert_correctness


def test_skip_assert():
    before_and_after = BeforeAndAfter(
        """
while 1:
    assert val
    foo()
""",
        "while 1:foo()",
    )

    optimize_and_assert_correctness(
        before_and_after, token_types_to_skip=TokenTypesToSkipConfig(skip_asserts=True)
    )
