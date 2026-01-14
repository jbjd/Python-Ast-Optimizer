from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_useless_try():
    before_and_after = BeforeAndAfter(
        """
try:
    pass
    pass
except Exception as e:
    pass
""",
        "",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_raise_same_line():
    before_and_after = BeforeAndAfter(
        """
try:
    a += 1
except (Exception, ValueError) as e:
    raise ValueError('a') from e
""",
        "try:a+=1\nexcept(Exception,ValueError)as e:raise ValueError('a')from e",
    )

    run_minifier_and_assert_correct(before_and_after)
