import pytest

from personal_python_ast_optimizer.parser.config import TokenTypesConfig
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_tuple_whitespace():
    before_and_after = BeforeAndAfter(
        """
if a in (1,2):
    print()
""",
        "if a in(1,2):print()",
    )

    run_minifier_and_assert_correct(before_and_after)


_simplify_named_tuple_test_cases: list[tuple[str, str]] = [
    (
        """
from typing import NamedTuple

class A(NamedTuple):
    foo: int
    bar: str
""",
        "from collections import namedtuple\nA=namedtuple('A',['foo','bar'])",
    ),
    (
        """
from collections import namedtuple
from typing import NamedTuple

class A(NamedTuple):
    foo: int
    bar: str
""",
        "from collections import namedtuple\nA=namedtuple('A',['foo','bar'])",
    ),
    (
        """
from collections import OrderedDict
from typing import NamedTuple

class A(NamedTuple):
    foo: int
    bar: str
b=OrderedDict()
""",
        "from collections import OrderedDict,namedtuple\nA=namedtuple('A',['foo','bar'])\nb=OrderedDict()",  # noqa: E501
    ),
]


@pytest.mark.parametrize(("before", "after"), _simplify_named_tuple_test_cases)
def test_simplify_named_tuple(before: str, after: str):
    before_and_after = BeforeAndAfter(before, after)

    run_minifier_and_assert_correct(
        before_and_after,
        token_types_config=TokenTypesConfig(simplify_named_tuples=True),
    )
