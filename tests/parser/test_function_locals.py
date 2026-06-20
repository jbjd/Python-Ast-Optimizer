from personal_python_ast_optimizer.parser.config import OptimizationsConfig
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_fold_function_locals():
    before: str = """
def get_byte_display(size_in_bytes):
    kb_size = 1000
    size_in_kb: int = size_in_bytes // kb_size
    return f"{size_in_kb / kb_size:.2f}mb" if size_in_kb > 999 else f"{size_in_kb}kb"
"""
    after: str = (
        "def get_byte_display(size_in_bytes):"
        "size_in_kb=size_in_bytes//1000;"
        "return f'{size_in_kb/1000:.2f}mb'if size_in_kb>999 else f'{size_in_kb}kb'"
    )

    run_minifier_and_assert_correct(
        BeforeAndAfter(before, after),
        optimizations_config=OptimizationsConfig(fold_simple_function_locals=True),
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

    run_minifier_and_assert_correct(
        BeforeAndAfter(before, after),
        optimizations_config=OptimizationsConfig(fold_simple_function_locals=True),
    )
