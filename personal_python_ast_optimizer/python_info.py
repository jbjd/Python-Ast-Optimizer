"""Various tokens in Python that the ast module writes"""

# Functions that have no side effects and thus are safe to remove
# if a test expression is found to be useless. For example:
# if "str(a) == 'a':pass" will be turned into just "str(a) == 'a'"
# but if its known str has no side effects then it can be fully removed
default_functions_safe_to_exclude_in_test_expr: set[str] = {
    "int",
    "str",
    "isinstance",
    "getattr",
    "hasattr",
}

comparison_and_conjunctions: list[str] = [
    " if ",
    " else ",
    " and ",
    " or ",
    " is ",
    " is not ",
    " in ",
    " not in ",
    " for ",
    " async for ",
    " from ",
    " as ",
]

operators_and_separators: list[str] = [
    ", ",
    " = ",
    " += ",
    " -= ",
    " *= ",
    " **= ",
    " /= ",
    " //= ",
    " %= ",
    " <<= ",
    " >>= ",
    " |= ",
    " &= ",
    " := ",
    ": ",
    " == ",
    " != ",
    " < ",
    " <= ",
    " > ",
    " >= ",
    " + ",
    " - ",
    " * ",
    " ** ",
    " / ",
    " // ",
    " % ",
    " << ",
    " >> ",
    " | ",
    " & ",
    " ^ ",
]

chars_that_dont_need_whitespace: list[str] = [
    "'",
    '"',
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    "*",
]
