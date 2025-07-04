from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_if_with_only_passes():
    before_and_after = BeforeAndAfter("if a == b:pass;pass", "")

    run_minifier_and_assert_correct(before_and_after)
