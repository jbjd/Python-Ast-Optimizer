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
        "if test():pass\nelse:pass",
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


_nested_if_cases = [
    BeforeAndAfter(
        """
if a < b and foo() or bar():
    if b < c:
        print()
""",
        "if(a<b and foo()or bar())and b<c:print()",
    ),
    BeforeAndAfter(
        """
if foo():
    if bar():
        print()
""",
        "if foo()and bar():print()",
    ),
    BeforeAndAfter(
        """
if a < b:
    if b < c:
        print()
    something_else()
""",
        """if a<b:
\tif b<c:print()
\tsomething_else()""",
    ),
    BeforeAndAfter(
        """
if a < b:
    if b < c:
        print()
else:
    something_else()
""",
        """if a<b:
\tif b<c:print()
else:something_else()""",
    ),
    BeforeAndAfter(
        """
if a < b:
    if b < c:
        print()
    else:
        something_else()
""",
        """if a<b:
\tif b<c:print()
\telse:something_else()""",
    ),
]


@pytest.mark.parametrize("before_and_after", _nested_if_cases)
def test_nested_if(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(before_and_after)


def test_if_return():
    before_and_after = BeforeAndAfter(
        """
def a(foo):
    if foo > 5:
        return 5
    elif foo < 9:
        return 6
    else:
        return 7""",
        """def a(foo):
\tif foo>5:return 5
\tif foo<9:return 6
\treturn 7""",
    )
    run_minifier_and_assert_correct(before_and_after)
