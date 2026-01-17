from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_useless_while():
    before_and_after = BeforeAndAfter(
        "while 0:\n\tfoo()",
        "",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_while_true():
    before_and_after = BeforeAndAfter(
        "while True:\n\tfoo()",
        "while 1:foo()",
    )

    run_minifier_and_assert_correct(before_and_after)
