import pytest

from personal_python_ast_optimizer.regex.replace import (
    RegexNoMatchError,
    RegexReplacement,
    re_replace,
)

_re_cases = [
    (
        RegexReplacement("series", "wonder"),
        "Some series of things. A real series.",
        "Some wonder of things. A real series.",
    ),
    (
        RegexReplacement("series", "wonder", count=0),
        "Some series of things. A real series.",
        "Some wonder of things. A real wonder.",
    ),
    (
        RegexReplacement("series", "wonder"),
        "Fox",
        "Fox",
    ),
]


@pytest.mark.parametrize(("replacement", "source", "expected_output"), _re_cases)
def test_re_replace(replacement: RegexReplacement, source: str, expected_output: str):
    assert re_replace(source, replacement) == expected_output


def test_re_replace_raises():
    with pytest.raises(RegexNoMatchError):
        re_replace(
            "Fox", RegexReplacement("series", "wonder"), raise_if_not_applied=True
        )
