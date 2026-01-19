from personal_python_ast_optimizer.regex.replace import RegexReplacement, re_replace


def test_re_replace():
    replacement = RegexReplacement("series", "wonder")
    re_input: str = "Some series of things. A real series."
    expected_re_output: str = "Some wonder of things. A real series."

    assert re_replace(re_input, replacement) == expected_re_output
