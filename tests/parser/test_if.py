from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_if_pass():
    before_and_after = BeforeAndAfter(
        """
if a == b:pass;pass
else:print()""",
        "print()",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_if_pass_with_elif():
    before_and_after = BeforeAndAfter(
        """
if a == b:pass
elif b == c:print()
else:print()""",
        """
if b==c:print()
else:print()
""".strip(),
    )

    run_minifier_and_assert_correct(before_and_after)


def test_elif_pass():
    before_and_after = BeforeAndAfter(
        """
if a == b:print()
elif b == c:pass
else:print()""",
        """
if a==b:print()
else:print()
""".strip(),
    )

    run_minifier_and_assert_correct(before_and_after)
