import os
import sys

import pytest

from personal_python_ast_optimizer.parser.config import ExtrasConfig
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_cpu_count_example: str = """
def get_cpu_count():
    return os.cpu_count() or 1
"""

_sys_example: str = f"N = '<' if sys.byteorder == '{sys.byteorder}' else '>'"


@pytest.mark.parametrize(
    "assume_this_machine,before,after",
    [
        (
            True,
            _cpu_count_example,
            f"def get_cpu_count():return {os.cpu_count()}",
        ),
        (False, _cpu_count_example, "def get_cpu_count():return os.cpu_count()or 1"),
        (True, _sys_example, "N='<'"),
        (False, _sys_example, f"N='<'if sys.byteorder=='{sys.byteorder}'else'>'"),
    ],
)
def test_assume_this_machine(assume_this_machine: bool, before: str, after: str):

    before_and_after = BeforeAndAfter(before, after)

    run_minifier_and_assert_correct(
        before_and_after,
        extras_config=ExtrasConfig(assume_this_machine=assume_this_machine),
    )
