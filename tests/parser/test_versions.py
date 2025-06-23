"""Optimizations that should only be used on a specific version"""

import pytest

from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


@pytest.mark.parametrize(
    "target_python_version,expected_output",
    [
        ((3, 0), "class Foo:pass"),
        (None, "class Foo(object):pass"),
    ],
)
def test_class_ignorable_bases(
    target_python_version: tuple[int, int] | None, expected_output: str
):
    before_and_after = BeforeAndAfter(
        """
class Foo(object):
    pass
""",
        expected_output,
    )

    run_minifier_and_assert_correct(
        before_and_after, target_python_version=target_python_version
    )
