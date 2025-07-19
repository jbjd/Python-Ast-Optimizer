from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_empty():
    empty_script = BeforeAndAfter("", "")
    run_minifier_and_assert_correct(empty_script)


def test_script_with_annotations():
    before_and_after = BeforeAndAfter("a: int;b: int = 2;b -= 1", "b=2\nb-=1")
    run_minifier_and_assert_correct(before_and_after)


def test_one_line_if():
    before_and_after = BeforeAndAfter(
        """
a if True else b
'a' if test == 'False' else 'b'
""",
        """
a if True else b
'a'if test=='False'else'b'
""".strip(),
    )
    run_minifier_and_assert_correct(before_and_after)


def test_module_doc_string():
    before_and_after = BeforeAndAfter(
        """\"\"\"some doc string\"\"\"
foo = 5
""",
        "foo=5",
    )
    run_minifier_and_assert_correct(before_and_after)


def test_inline_all():
    before_and_after = BeforeAndAfter(
        """
if b==1:
    assert True
    a = 1
    a += 1
    break
    continue
    del a
    c()
    import foo
    from spam import eggs
    pass
    raise Exception
    return 0
""",
        (
            "if b==1:assert True;a=1;a+=1;break;continue;del a;c();import foo;"
            "from spam import eggs;raise Exception;return 0"
        ),
    )
    run_minifier_and_assert_correct(before_and_after)
