from personal_python_ast_optimizer._optimize.utils import UglyNameGenerator


def test_ugly_name_generator():
    """Should handle moving between names of different lengths."""
    name_generator = UglyNameGenerator()

    assert name_generator.get_ugly_name() == "a"
    assert name_generator.get_ugly_name() == "b"

    for _ in range(50):
        name_generator.get_ugly_name()

    assert name_generator.get_ugly_name() == "aa"
