from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_if_with_only_passes():
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
