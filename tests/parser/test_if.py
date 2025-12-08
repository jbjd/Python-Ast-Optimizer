import pytest

from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_if_cases = [
    BeforeAndAfter(
        """
if a() == b:pass
else:pass
""",
        "if a()==b:pass",
    ),
    BeforeAndAfter(
        """
if a == b:pass
else:print()""",
        """
if a==b:pass
else:print()
""".strip(),
    ),
    BeforeAndAfter(
        """
if True:foo()
else: bar()""",
        "foo()",
    ),
    BeforeAndAfter(
        """
if False:foo()
else: bar()""",
        "bar()",
    ),
    BeforeAndAfter(
        """
if False:foo()
elif True: test()
else: bar()""",
        "test()",
    ),
    BeforeAndAfter(
        """
if func_with_side_effect():foo()
elif func_with_side_effect2():test()
elif True: test2()
elif func_with_side_effect3():test3()
else: bar()""",
        """
if func_with_side_effect():foo()
elif func_with_side_effect2():test()
else:test2()""".strip(),
    ),
]


@pytest.mark.parametrize("before_and_after", _if_cases)
def test_if(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(before_and_after)
