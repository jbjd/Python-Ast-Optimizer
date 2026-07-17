import pytest

from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
if a() == b:eggs()
else:pass
""",
            "if a()==b:eggs()",
        ),
        (
            """
if a == b:eggs()
else:print()""",
            "if a==b:eggs()\nelse:print()",
        ),
        (
            """
if 1 == 1:foo()
else: bar()""",
            "foo()",
        ),
        (
            """
if 1 == 2:foo()
else: bar()""",
            "bar()",
        ),
        (
            """
if False:foo()
elif True: test()
else: bar()""",
            "test()",
        ),
        (
            """
if func_with_side_effect():foo()
elif func_with_side_effect2():test()
elif True: test2()
elif func_with_side_effect3():test3()
else: bar()""",
            """
if func_with_side_effect():foo()
elif func_with_side_effect2():test()
else:test2()""".lstrip(),
        ),
        (
            "if test():pass\nelse:foo()",
            "if test():pass\nelse:foo()",
        ),
        (
            "if test(a()) and b():pass\nelse:pass",
            "test(a())\nb()",
        ),
        (
            "if str(a) == 'a':pass",
            "",
        ),
        (
            """
'a' if 'True' == b else 'b'
a='a' if 1==1 else 'b'
b='a' if 1==2 else 'b'
""",
            "'a'if'True'==b else'b'\na='a'\nb='b'",
        ),
    ],
)
def test_if(source: str, expected: str):
    """Should remove dead if nodes and preserve functions with side-effects."""

    optimize_and_assert_correctness(source, expected)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
if foo():
    if bar():
        print()
""",
            "if foo()and bar():print()",
        ),
        (
            """
if foo() and spam():
    if bar():
        print()
""",
            "if foo()and spam()and bar():print()",
        ),
        (
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
        (
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
    ],
)
def test_nested_if(source: str, expected: str):
    """Should condense unnecessary ifs."""

    optimize_and_assert_correctness(source, expected)


def test_else_return():
    """Should remove else-returns."""

    source: str = """
def a(foo):
    if foo > 5:
        raise ValueError
    elif foo < 9:
        return 6
    else:
        return 7"""

    expected: str = """def a(foo):
\tif foo>5:raise ValueError
\tif foo<9:return 6
\treturn 7"""

    optimize_and_assert_correctness(source, expected)
