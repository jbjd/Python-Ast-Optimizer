from tests.utils import BeforeAndAfter, optimize_and_assert_correctness


def test_almost_useful_try():
    before_and_after = BeforeAndAfter(
        """
try:
    pass
    pass
except:
    pass
finally:
    print(1)
""",
        "print(1)",
    )

    optimize_and_assert_correctness(before_and_after)


def test_useless_try():
    before_and_after = BeforeAndAfter(
        """
try:
    pass
except Exception as e:
    pass
finally:
    pass
""",
        "",
    )

    optimize_and_assert_correctness(before_and_after)
