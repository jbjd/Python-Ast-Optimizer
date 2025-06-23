import pytest

from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


_all_futures_imports: str = """
from __future__ import annotations
from __future__ import generator_stop
from __future__ import unicode_literals
from __future__ import with_statement
"""


@pytest.mark.parametrize(
    "target_python_version,expected_output",
    [
        ((3, 7), ""),
        (None, _all_futures_imports.strip()),
    ],
)
def test_futures_imports(
    target_python_version: tuple[int, int] | None, expected_output: str
):

    before_and_after = BeforeAndAfter(_all_futures_imports, expected_output)

    run_minifier_and_assert_correct(
        before_and_after, target_python_version=target_python_version
    )


def test_import_same_line():

    before_and_after = BeforeAndAfter(
        """
def i():
    import a
    from b import c
    import d
""",
        "def i():import a;from b import c;import d",
    )
    run_minifier_and_assert_correct(before_and_after)


def test_import_star():

    before_and_after = BeforeAndAfter(
        "from ctypes import *",
        "from ctypes import*",
    )
    run_minifier_and_assert_correct(before_and_after)
