from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_raise_same_line():
    before_and_after = BeforeAndAfter(
        """
try:
    pass
except (Exception, ValueError) as e:
    raise ValueError('a') from e
""",
        "try:pass\nexcept(Exception,ValueError)as e:raise ValueError('a')from e",
    )

    run_minifier_and_assert_correct(before_and_after)
