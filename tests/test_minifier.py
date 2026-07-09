from tests.utils import minify_and_assert_correctness


def test_long_script():
    """Should output code in a minified format without syntax errors."""

    before: str = """
type FileName = str
class File:
    \"\"\"a file\"\"\"
    KB: int

    def __init__(self, name: FileName) -> None:
        self.name: FileName = name

if __name__ == "__main__":
    files = [ File(str(n)) for n in range(10) ]
    print(files)
"""
    after: str = """
type FileName=str
class File:
    \"\"\"a file\"\"\"
    KB:int
    def __init__(self,name:FileName)->None:self.name:FileName=name
if __name__=='__main__':files=[File(str(n))for n in range(10)];print(files)
""".strip().replace("    ", "\t")
    minify_and_assert_correctness(before, after)


def test_inlining():
    """Should inline all applicable nodes with semicolon delimitors."""

    before: str = """
def a():
    global b
    nonlocal c
    assert True
    a = 1
    a += 1
    break
    continue
    del a
    some_func()
    import foo
    from spam import eggs
    pass
    raise Exception
    return 0
"""
    after = (
        "def a():global b;nonlocal c;assert True;a=1;a+=1;break;continue;del a;"
        "some_func();import foo;from spam import eggs;pass;raise Exception;return 0"
    )
    minify_and_assert_correctness(before, after)


def test_dangling_expression1():
    minify_and_assert_correctness(
        '''def a():
    """some doc string"""
    foo = 5
    bar = 6
''',
        '''def a():
\t"""some doc string"""
\tfoo=5;bar=6''',
    )


def test_dangling_expression2():
    minify_and_assert_correctness(
        '''def a():
    """some
doc string"""
    if 1: print(1)
''',
        '''def a():
\t"""some
doc string"""
\tif 1:print(1)''',
    )
