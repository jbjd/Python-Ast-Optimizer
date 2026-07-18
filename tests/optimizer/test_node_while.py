from tests.utils import optimize_and_assert_correctness


def test_useless_while():
    """Should remove dead while loop."""

    optimize_and_assert_correctness("while 0:\n\tfoo()", "")


def test_while_true():
    """Should change `while True:` to `while 1:`."""

    optimize_and_assert_correctness("while True:\n\tfoo()", "while 1:foo()")
