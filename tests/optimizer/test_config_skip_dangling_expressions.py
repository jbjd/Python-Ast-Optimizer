from personal_python_ast_optimizer.config import (
    PerfOptimizationsConfig,
    TokenTypesToSkipConfig,
)
from tests.utils import optimize_and_assert_correctness

_DANGLING_EXPRESSIONS_EXAMPLE: str = '''
def a():
    """asdf"""
class A:
    """asdf"""
    2+6
'''


def test_skip_dangling_expressions():
    """Should remove dangling expressions from body."""
    optimize_and_assert_correctness(
        _DANGLING_EXPRESSIONS_EXAMPLE,
        "def a():pass\nclass A:pass",
        token_types_to_skip=TokenTypesToSkipConfig(skip_dangling_expressions=True),
        perf_optimizations=PerfOptimizationsConfig(fold_constants=True),
    )


def test_no_skip_dangling_expressions():
    """Should not remove dangling expressions from body."""
    optimize_and_assert_correctness(
        _DANGLING_EXPRESSIONS_EXAMPLE,
        '''def a():
\t"""asdf"""
class A:
\t"""asdf"""
\t2+6''',
        token_types_to_skip=TokenTypesToSkipConfig(skip_dangling_expressions=False),
    )
