from tests.utils import optimize_and_assert_correctness


def test_empty():
    optimize_and_assert_correctness("", "")
