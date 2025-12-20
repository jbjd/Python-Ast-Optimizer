from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_global_same_line():
    before_and_after = BeforeAndAfter(
        """
a = 1
def test():
    global a
    print(a)
""",
        "a=1\ndef test():global a;print(a)",
    )

    run_minifier_and_assert_correct(before_and_after)


def test_nonlocal_same_line():
    before_and_after = BeforeAndAfter(
        """
def test():
    x = 1
    def i():
        nonlocal x
        print(x)
    i()
""",
        """
def test():
    x = 1
    def i():nonlocal x;print(x)
    i()""".strip(),
    )

    run_minifier_and_assert_correct(before_and_after)
