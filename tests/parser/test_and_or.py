from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_or_useless():
    before_and_after = BeforeAndAfter(
        """
def test_foo():
    return "" or 2 or 1 and 0
""",
        "def test_foo():return 2",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_or_all_false():
    before_and_after = BeforeAndAfter(
        """
def test_foo():
    return "" or 0
""",
        "def test_foo():return 0",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_and_useless():
    before_and_after = BeforeAndAfter(
        """
def test_foo():
    return 1 and 0 and 1
""",
        "def test_foo():return 0",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_and_all_true():
    before_and_after = BeforeAndAfter(
        """
def test_foo():
    return 1 and 2 and 3
""",
        "def test_foo():return 3",
    )

    run_minifier_and_assert_correct(before_and_after)
