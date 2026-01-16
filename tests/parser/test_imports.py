import pytest

from personal_python_ast_optimizer.parser.config import (
    OptimizationsConfig,
    TokenTypesConfig,
    TypeHintsToSkip,
)
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_futures_imports: str = """
from __future__ import annotations
from __future__ import generator_stop
from __future__ import unicode_literals
from __future__ import with_statement
"""

_futures_imports_inline: str = (
    "from __future__ import annotations,generator_stop,unicode_literals,with_statement"
)


@pytest.mark.parametrize(
    "version,skip_type_hints,after",
    [
        (None, TypeHintsToSkip.NONE, _futures_imports_inline),
        ((3, 7), TypeHintsToSkip.NONE, "from __future__ import annotations"),
        ((3, 7), TypeHintsToSkip.ALL, ""),
    ],
)
def test_futures_imports(
    version: tuple[int, int] | None, skip_type_hints: TypeHintsToSkip, after: str
):
    before_and_after = BeforeAndAfter(_futures_imports, after)

    run_minifier_and_assert_correct(
        before_and_after,
        target_python_version=version,
        token_types_config=TokenTypesConfig(skip_type_hints=skip_type_hints),
    )


def test_import_same_line():
    before_and_after = BeforeAndAfter(
        """
import test
import test2
def i():
    import a
    import d
    from b import c
    from b import d as e
    from .b import f
    print()
    import e
""",
        """import test,test2
def i():import a,d;from b import c,d as e;from .b import f;print();import e""",
    )
    run_minifier_and_assert_correct(
        before_and_after,
        optimizations_config=OptimizationsConfig(remove_unused_imports=False),
    )


def test_import_star():
    before_and_after = BeforeAndAfter(
        "from ctypes import *",
        "from ctypes import*",
    )
    run_minifier_and_assert_correct(
        before_and_after,
        optimizations_config=OptimizationsConfig(remove_unused_imports=False),
    )


_unused_import_test_cases: list[BeforeAndAfter] = [
    BeforeAndAfter(
        """
if a == b:
    import foo
    import bar

print(a)""",
        "if a==b:pass\nprint(a)",
    ),
    BeforeAndAfter(
        """
import foo

a: foo = bar()

def asdf(a: foo) -> foo:
    return a""",
        """
a=bar()
def asdf(a):return a
""".strip(),
    ),
    BeforeAndAfter(
        """
from .typing import foo

a: foo | None = bar()

def asdf(a: foo) -> foo:
    return a""",
        """
a=bar()
def asdf(a):return a
""".strip(),
    ),
    BeforeAndAfter(
        """
from foo import bar as bar2

if False:
    bar2()

bar()
""".strip(),
        "bar()",
    ),
]


@pytest.mark.parametrize("before_and_after", _unused_import_test_cases)
def test_remove_unused_import(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(before_and_after)
