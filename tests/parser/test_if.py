from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_if_with_only_passes():
    before_and_after = BeforeAndAfter(
        """
if a == b:pass;pass
print()""",
        "print()",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_if_pass_with_elif():
    """Should not remove if:pass if it changes semantics
    like when an else would trigger"""
    before_and_after = BeforeAndAfter(
        """
if a == b:pass
else:print()""",
        """
if a==b:pass
else:print()
""".strip(),
    )

    run_minifier_and_assert_correct(before_and_after)
