from tests.utils import BeforeAndAfter, optimize_and_assert_correct


def test_continue_same_line():
    before_and_after = BeforeAndAfter(
        """
if a > 6:
    continue
""",
        "if a>6:continue",
    )

    optimize_and_assert_correct(before_and_after)
