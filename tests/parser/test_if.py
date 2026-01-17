import pytest

from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_if_cases = [
    BeforeAndAfter(
        """
if a() == b:eggs()
else:pass
""",
        "if a()==b:eggs()",
    ),
    BeforeAndAfter(
        """
if a == b:eggs()
else:print()""",
        """
if a==b:eggs()
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
    BeforeAndAfter(
        """
if 1 != 2:foo()
else:bar()""",
        "foo()",
    ),
    BeforeAndAfter(
        "if test():pass\nelse:foo()",
        "if test():pass\nelse:foo()",
    ),
    BeforeAndAfter(
        "if test():pass",
        "test()",
    ),
    BeforeAndAfter(
        "if str(a) == 'a':pass",
        "",
    ),
    BeforeAndAfter(
        "if a < 3:pass",
        "",
    ),
    BeforeAndAfter(
        """
try:foo()
except:raise OSError
if test():pass""",
        "try:foo()\nexcept:raise OSError\ntest()",
    ),
]


@pytest.mark.parametrize("before_and_after", _if_cases)
def test_if(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(before_and_after)
