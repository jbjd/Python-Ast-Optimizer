"""Various tokens in Python that the ast module writes"""

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
