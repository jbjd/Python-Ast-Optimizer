import pytest

from personal_python_ast_optimizer.config import (
    PerfOptimizationsConfig,
    TokenTypesToSkipConfig,
    TypeHintsToSkip,
)
from tests.utils import optimize_and_assert_correctness, optimize_expect_error

_example_named_tuple: str = """from typing import NamedTuple
class A(NamedTuple):foo:int;bar:str"""


def test_no_simplify_named_tuple():
    """Should not change simple NamedTuples to namedtuple."""
    optimize_and_assert_correctness(
        _example_named_tuple,
        _example_named_tuple,
        perf_optimizations=PerfOptimizationsConfig(simplify_named_tuple=False),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            _example_named_tuple,
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
    ],
)
def test_simplify_named_tuple(source: str, expected: str):
    """Should change simple NamedTuples to namedtuple."""
    optimize_and_assert_correctness(
        source,
        expected,
        token_types_to_skip=TokenTypesToSkipConfig(skip_type_hints=TypeHintsToSkip.ALL),
        perf_optimizations=PerfOptimizationsConfig(simplify_named_tuple=True),
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
