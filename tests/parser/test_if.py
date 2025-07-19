import pytest
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_if_with_dead_code_cases = [
    ("if 'j'=='p'and 1==5 and True or False:print()", ""),
    ("if True:print()", "print()"),
    ("if True:pass", ""),
    (
        """
if False:print()
else:exit()
""",
        "exit()",
    ),
    (
        """
if False:print()
elif True and False: foo()
elif True: bar()
elif a==b: spam()
else:exit()
""",
        "bar()",
    ),
    (
        """
if a==b: spam()
elif True: bar()
""",
        "if a==b:spam()\nelse:bar()",
    ),
]


@pytest.mark.parametrize("before,after", _if_with_dead_code_cases)
def test_if_with_dead_code(before: str, after: str):

    before_and_after = BeforeAndAfter(before, after)

    run_minifier_and_assert_correct(before_and_after)


_if_pass_cases = [
    (
        """
if a() == b:pass
else:pass
""",
        "if a()==b:pass",
    ),
    (
        """
if a == b:pass
else:print()""",
        """
if a==b:pass
else:print()
""".strip(),
    ),
]


@pytest.mark.parametrize("before,after", _if_pass_cases)
def test_if_pass(before: str, after: str):
    """Should remove else:pass nodes when possible"""

    before_and_after = BeforeAndAfter(before, after)
    run_minifier_and_assert_correct(before_and_after)
