from personal_python_ast_optimizer.config import TokenTypesToSkipConfig, TypeHintsToSkip
from tests.utils import optimize_and_assert_correctness


def test_not_simple_ann_assign():
    """Should wrap AnnAssign in parenthesis."""
    optimize_and_assert_correctness(
        "(a): int = 1",
        "(a):int=1",
        token_types_to_skip=TokenTypesToSkipConfig(
            skip_type_hints=TypeHintsToSkip.NONE
        ),
    )
