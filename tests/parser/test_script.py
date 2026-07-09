from tests.utils import BeforeAndAfter, optimize_and_assert_correctness_old


def test_empty():
    empty_script = BeforeAndAfter("", "")
    optimize_and_assert_correctness_old(empty_script)


def test_one_line_if():
    before_and_after = BeforeAndAfter(
        """
'a' if 'True' == b else 'b'
'a' if b == 'True' else 'b'
a='a' if 1==1 else 'b'
b='a' if 1==2 else 'b'
""",
        """
'a'if'True'==b else'b'
'a'if b=='True'else'b'
a='a'
b='b'
""".strip(),
    )
    optimize_and_assert_correctness_old(before_and_after)
