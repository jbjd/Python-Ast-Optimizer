from enum import IntEnum, StrEnum

import pytest

from personal_python_ast_optimizer.parser.config import OptimizationsConfig
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


class _SomeIntEnum(IntEnum):
    A = 1
    B = 2


class _SomeStrEnum(StrEnum):
    C = "C"
    D = "D"


_fold_enum_cases = [
    BeforeAndAfter(
        """
class _SomeIntEnum(IntEnum):
    A = 1
    B = 2

print(_SomeIntEnum.A)""",
        "print(1)",
    ),
    BeforeAndAfter(
        """
from somewhere import _SomeStrEnum

print(_SomeStrEnum.C)""",
        "print('C')",
    ),
    BeforeAndAfter(
        """
import somewhere

print(somewhere.someModule._SomeStrEnum.C)""",
        """
import somewhere
print('C')""".strip(),
    ),
]


@pytest.mark.parametrize("before_and_after", _fold_enum_cases)
def test_fold_enum(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(
        before_and_after,
        optimizations_config=OptimizationsConfig(
            enums_to_fold={_SomeIntEnum, _SomeStrEnum}
        ),
    )
