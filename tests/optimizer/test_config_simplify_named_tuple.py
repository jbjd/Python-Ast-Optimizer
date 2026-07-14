import pytest

from personal_python_ast_optimizer.config import PerfOptimizationsConfig
from tests.utils import optimize_and_assert_correctness, optimize_expect_error

_example_named_tuple: str = """from typing import NamedTuple
class A(NamedTuple):foo:int;bar:str"""


@pytest.mark.parametrize(
    ("source", "expected", "simplify_named_tuple"),
    [
        (
            _example_named_tuple,
            _example_named_tuple,
            False,
        ),
        (
            _example_named_tuple,
            "from collections import namedtuple\nA=namedtuple('A',['foo','bar'])",
            True,
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
            True,
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
            True,
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
            True,
        ),
    ],
)
def test_simplify_named_tuple(source: str, expected: str, simplify_named_tuple: bool):
    """Should change simple NamedTuples to namedtuple."""
    optimize_and_assert_correctness(
        source,
        expected,
        perf_optimizations=PerfOptimizationsConfig(
            simplify_named_tuple=simplify_named_tuple
        ),
    )


def test_simplify_named_tuple_error():
    """Should error when default values are set incorrectly."""

    source: str = """
from typing import NamedTuple

class A(NamedTuple):
    foo: int = 2
    bar: int
    spam: str = 'a'
"""

    optimize_expect_error(
        source,
        ValueError,
        'namedtuple "A" has non-default following a default field',
        perf_optimizations=PerfOptimizationsConfig(simplify_named_tuple=True),
    )
