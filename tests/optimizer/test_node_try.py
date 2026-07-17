from tests.utils import optimize_and_assert_correctness


def test_try_star():
    """Should not remove useful try and finally clause."""
    optimize_and_assert_correctness(
        """
try:
    some_func()
except* ValueError:
    print ('v')
except* TypeError as e:
    print('t')
finally:
    on_end()
""",
        """try:some_func()
except*ValueError:print('v')
except*TypeError as e:print('t')
finally:on_end()""",
    )


def test_useless_try_useless_finally():
    """Should remove useless try and finally clause."""
    optimize_and_assert_correctness(
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


def test_useless_try_useful_finally():
    """Should remove useless try and keep what's in finally clause."""
    optimize_and_assert_correctness(
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
