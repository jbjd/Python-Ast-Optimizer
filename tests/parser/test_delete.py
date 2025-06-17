from tests.utils import BeforeAndAfter, run_minifiyer_and_assert_correct


def test_assert_same_line():
    before_and_after = BeforeAndAfter(
        """
def test_foo(a,b,c):
    del a
    del b
    del c
""",
        "def test_foo(a,b,c):\n\tdel a;del b;del c",
    )

    run_minifiyer_and_assert_correct(before_and_after)
