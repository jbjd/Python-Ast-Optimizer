from personal_python_ast_optimizer.config import (
    PerfOptimizationsConfig,
    TokenTypesToSkipConfig,
    TypeHintsToSkip,
)
from tests.utils import optimize_and_assert_correctness


def test_fold_function_locals():
    before: str = """
def get_byte_display():
    byte_size = 9999
    kb_size: int = 1000
    size_in_kb: int = byte_size // kb_size
    return f"{size_in_kb / kb_size:.2f}mb" if size_in_kb > 999 else f"{size_in_kb}kb"
"""
    after: str = "def get_byte_display():return f'{9}kb'"

    optimize_and_assert_correctness(
        before,
        after,
        token_types_to_skip=TokenTypesToSkipConfig(
            skip_type_hints=TypeHintsToSkip.NONE
        ),
        perf_optimizations=PerfOptimizationsConfig(
            fold_constants=True, fold_simple_function_locals=True
        ),
    )


def test_fold_if_else_unpack():
    before: str = """
def asdf(a,scaling):
    if a:limit=1
    else:scaling,limit=scaling
    print(limit)
"""
    after: str = """def asdf(a,scaling):
\tif a:limit=1
\telse:scaling,limit=scaling
\tprint(limit)"""

    optimize_and_assert_correctness(
        before,
        after,
        perf_optimizations=PerfOptimizationsConfig(fold_simple_function_locals=True),
    )


def test_fold_params():
    before: str = """
def asdf(a):
    a=1
    print(a)
"""
    after: str = """def asdf(a):a=1;print(a)"""

    optimize_and_assert_correctness(
        before,
        after,
        perf_optimizations=PerfOptimizationsConfig(fold_simple_function_locals=True),
    )


def test_fold_named_aug_assign():
    before: str = """
def asdf():
    a=2
    a+=4
    print(a)
"""
    after: str = """def asdf():a=2;a+=4;print(a)"""

    optimize_and_assert_correctness(
        before,
        after,
        perf_optimizations=PerfOptimizationsConfig(fold_simple_function_locals=True),
    )


def test_fold_named_expr():
    before: str = """
def asdf():
    a=2
    print(a := 1)
    print(a)
"""
    after: str = """def asdf():a=2;print((a:=1));print(a)"""

    optimize_and_assert_correctness(
        before,
        after,
        perf_optimizations=PerfOptimizationsConfig(fold_simple_function_locals=True),
    )


def test_fold_globals_non_locals():
    """Should not fold globals/nonlocals."""

    before: str = """
def asdf():
    global b
    b=None
    c=1
    def qwer():
        nonlocal c
        print(c)
    return a or qwer()"""

    after: str = """def asdf():
\tglobal b;b=None;c=1
\tdef qwer():nonlocal c;print(c)
\treturn a or qwer()"""

    optimize_and_assert_correctness(
        before,
        after,
        perf_optimizations=PerfOptimizationsConfig(fold_simple_function_locals=True),
    )


def test_fold_none():
    before: str = """
def asdf():
    a=None
    return a or 3
"""
    after: str = """def asdf():return 3"""

    optimize_and_assert_correctness(
        before,
        after,
        perf_optimizations=PerfOptimizationsConfig(fold_simple_function_locals=True),
    )
