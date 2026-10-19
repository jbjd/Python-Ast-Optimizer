from personal_python_ast_optimizer.config import TokenTypesToSkipConfig, TypeHintsToSkip
from tests.utils import optimize_and_assert_correctness


def test_class_with_bases():
    """Should correctly unparse classes with different types of bases."""
    optimize_and_assert_correctness(
        "class ImageFile(Image.Image, metaclass=abc.ABCMeta):pass",
        "class ImageFile(Image.Image,metaclass=abc.ABCMeta):pass",
        token_types_to_skip=TokenTypesToSkipConfig(
            skip_type_hints=TypeHintsToSkip.NONE
        ),
    )
