"""Optimizations that should only be used on a specific version"""

from tests.utils import (
    BeforeAndAfterBasedOnVersion,
    run_minifier_and_assert_correct_multiple_versions,
)


def test_class_ignorable_bases():
    before_and_after = BeforeAndAfterBasedOnVersion(
        """
class Foo(object):
    pass
""",
        {"3.0": "class Foo:pass", None: "class Foo(object):pass"},
    )

    run_minifier_and_assert_correct_multiple_versions(before_and_after)
