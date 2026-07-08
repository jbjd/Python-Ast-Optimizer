from tests.utils import minify_and_validate_syntax


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
    minify_and_validate_syntax(before, after)


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
    minify_and_validate_syntax(before, after)
