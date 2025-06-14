from tests.utils import (
    BeforeAndAfter,
    BeforeAndAfterBasedOnVersion,
    run_minifiyer_and_assert_correct,
    run_minifiyer_and_assert_correct_multiple_versions,
)


def test_futures_imports():

    many_futures_imports: str = """
from __future__ import annotations
from __future__ import generator_stop
from __future__ import unicode_literals
from __future__ import with_statement
"""

    before_and_after = BeforeAndAfterBasedOnVersion(
        many_futures_imports,
        {"3.7": "", None: many_futures_imports.strip()},
    )

    run_minifiyer_and_assert_correct_multiple_versions(before_and_after)


def test_import_same_line():

    before_and_after: str = BeforeAndAfter(
        """
def i():
    import a
    from b import c
    import d
""",
        "def i():\n\timport a;from b import c;import d",
    )
    run_minifiyer_and_assert_correct(before_and_after)
