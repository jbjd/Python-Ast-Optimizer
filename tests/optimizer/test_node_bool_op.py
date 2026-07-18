from tests.utils import optimize_and_assert_correctness


def test_useless_or():
    """Should remove 'or' conditionals and stop at first truthy value."""
    optimize_and_assert_correctness(*_get_test_inputs("'' or 2 or 1 and 0", "2"))


def test_or_all_false():
    """Should remove 'or' conditionals and stop at last value."""
    optimize_and_assert_correctness(*_get_test_inputs("'' or 0", "0"))


def test_or_some_false():
    """Should remove 'or' conditionals and stop at last value."""
    optimize_and_assert_correctness(
        *_get_test_inputs("'' or 0 or func() or 2", "func()or 2")
    )


def test_useless_and():
    """Should remove 'and' conditionals and stop at first falsey value."""
    optimize_and_assert_correctness(*_get_test_inputs("1 and 0 and 1", "0"))


def test_and_all_true():
    """Should remove 'and' conditionals and stop at last value."""
    optimize_and_assert_correctness(*_get_test_inputs("1 and 2 and 3", "3"))


def _get_test_inputs(condition: str, expected: str) -> tuple[str, str]:
    return (
        f"""
def test_foo():
    return {condition}
""",
        f"def test_foo():return {expected}",
    )
