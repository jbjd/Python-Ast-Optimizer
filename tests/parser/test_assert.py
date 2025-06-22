from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_assert_same_line():
    before_and_after = BeforeAndAfter(
        """
def test_foo():
    assert 1
    assert 2, "bar"
    assert 3
""",
        "def test_foo():assert 1;assert 2,'bar';assert 3",
    )

    run_minifier_and_assert_correct(before_and_after)
