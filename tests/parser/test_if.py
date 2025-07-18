from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_if_else_pass():
    before_and_after = BeforeAndAfter(
        """
if a() == b:pass
else:pass
""",
        "if a()==b:pass",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_if_pass():
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
