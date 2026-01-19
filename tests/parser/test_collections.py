import pytest

from personal_python_ast_optimizer.parser.config import OptimizationsConfig
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

    run_minifier_and_assert_correct(
        before_and_after,
        optimizations_config=OptimizationsConfig(simplify_named_tuples=True),
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

    with pytest.raises(ValueError):
        run_minifier_and_assert_correct(
            before_and_after,
            optimizations_config=OptimizationsConfig(simplify_named_tuples=True),
        )


_collection_concat_to_unpack_test_cases: list[tuple[str, str]] = [
    (
        "a = (1,) + (0,0) + b",
        "a=(1,0,0,*b)",
    ),
    (
        "a = [1] + b + [2]",
        "a=[1,*b,2]",
    ),
    (
        "a = b + [2] + [3]",
        "a=[*b,2,3]",
    ),
]


@pytest.mark.parametrize(("before", "after"), _collection_concat_to_unpack_test_cases)
def test_collection_concat_to_unpack(before: str, after: str):
    before_and_after = BeforeAndAfter(before, after)

    run_minifier_and_assert_correct(
        before_and_after,
        optimizations_config=OptimizationsConfig(collection_concat_to_unpack=True),
    )
