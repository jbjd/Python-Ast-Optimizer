import os
import sys

import pytest

from personal_python_ast_optimizer.parser.config import OptimizationsConfig
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_cpu_count_example: str = """
def get_cpu_count():
    return os.cpu_count() or 1
"""

_os_name_example: str = "print(os.name)"

_sys_example: str = f"""
N = '<' if sys.byteorder == '{sys.byteorder}' else '>'
print(sys.platform == 'a')
"""


@pytest.mark.parametrize(
    "assume_this_machine,before,after",
    [
        (
            True,
            _cpu_count_example,
            f"def get_cpu_count():return {os.cpu_count()}",
        ),
        (False, _cpu_count_example, "def get_cpu_count():return os.cpu_count()or 1"),
        (True, _sys_example, "N='<'\nprint(False)"),
        (
            False,
            _sys_example,
            f"N='<'if sys.byteorder=='{sys.byteorder}'else'>'"
            "\nprint(sys.platform=='a')",
        ),
        (True, _os_name_example, f"print('{os.name}')"),
        (False, _os_name_example, _os_name_example),
    ],
)
def test_assume_this_machine(assume_this_machine: bool, before: str, after: str):
    before_and_after = BeforeAndAfter(before, after)

    run_minifier_and_assert_correct(
        before_and_after,
        optimizations_config=OptimizationsConfig(
            assume_this_machine=assume_this_machine
        ),
    )
