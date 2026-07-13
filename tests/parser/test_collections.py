import pytest

from personal_python_ast_optimizer.config import PerfOptimizationsConfig
from tests.utils import BeforeAndAfter, optimize_and_assert_correctness_old

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
    (
        """
from typing import NamedTuple

class A(NamedTuple):
    foo: int
    bar: int = 2
    spam: str = 'a'
""",
        "from collections import namedtuple\nA=namedtuple('A',['foo','bar','spam'],defaults=[2,'a'])",  # noqa: E501
    ),
]


@pytest.mark.parametrize(("before", "after"), _simplify_named_tuple_test_cases)
def test_simplify_named_tuple(before: str, after: str):
    before_and_after = BeforeAndAfter(before, after)

    optimize_and_assert_correctness_old(
        before_and_after,
        perf_optimizations=PerfOptimizationsConfig(simplify_named_tuples=True),
    )


def test_simplify_named_tuple_error():
    before_and_after = BeforeAndAfter(
        """
from typing import NamedTuple

class A(NamedTuple):
    foo: int = 2
    bar: int
    spam: str = 'a'
""",
        "",
    )

    with pytest.raises(
        ValueError,
        match='Non-default namedtuple "A" field "bar" cannot follow default field',
    ):
        optimize_and_assert_correctness_old(
            before_and_after,
            perf_optimizations=PerfOptimizationsConfig(simplify_named_tuples=True),
        )
