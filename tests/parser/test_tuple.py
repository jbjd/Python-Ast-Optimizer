from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_tuple_whitespace():
    before_and_after = BeforeAndAfter(
        """
if a in (1,2):
    print()
""",
        "if a in(1,2):print()",
    )

    run_minifier_and_assert_correct(before_and_after)
