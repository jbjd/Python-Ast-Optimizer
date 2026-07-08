from personal_python_ast_optimizer.config import CodeToFoldConfig
from tests.utils import BeforeAndAfter, optimize_and_assert_correctness


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

    optimize_and_assert_correctness(
        BeforeAndAfter(before, after),
        code_to_fold_config=CodeToFoldConfig(fold_simple_function_locals=True),
    )


def test_fold_function_locals_annotation():
    before: str = """
def asdf():
    a:int = 1
    print(a)
"""
    after: str = "def asdf():print(1)"

    optimize_and_assert_correctness(
        BeforeAndAfter(before, after),
        code_to_fold_config=CodeToFoldConfig(fold_simple_function_locals=True),
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
        BeforeAndAfter(before, after),
        code_to_fold_config=CodeToFoldConfig(fold_simple_function_locals=True),
    )


def test_fold_params():
    before: str = """
def asdf(a):
    a=1
    print(a)
"""
    after: str = """def asdf(a):a=1;print(a)"""

    optimize_and_assert_correctness(
        BeforeAndAfter(before, after),
        code_to_fold_config=CodeToFoldConfig(fold_simple_function_locals=True),
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
        BeforeAndAfter(before, after),
        code_to_fold_config=CodeToFoldConfig(fold_simple_function_locals=True),
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
        BeforeAndAfter(before, after),
        code_to_fold_config=CodeToFoldConfig(fold_simple_function_locals=True),
    )


def test_fold_none():
    before: str = """
def asdf():
    a=None
    return a or 3
"""
    after: str = """def asdf():return 3"""

    optimize_and_assert_correctness(
        BeforeAndAfter(before, after),
        code_to_fold_config=CodeToFoldConfig(fold_simple_function_locals=True),
    )
