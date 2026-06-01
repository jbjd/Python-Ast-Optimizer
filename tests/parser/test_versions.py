"""Optimizations that should only be used on a specific version"""

import pytest

from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


@pytest.mark.parametrize(
    ("version", "after"), [(None, "class Foo(object):pass"), ((3, 0), "class Foo:pass")]
)
def test_class_ignorable_bases(version: tuple[int, int] | None, after: str):
    before_and_after = BeforeAndAfter(
        """
class Foo(object):
    pass
""",
        after,
    )

    run_minifier_and_assert_correct(before_and_after, target_python_version=version)
