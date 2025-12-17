# Personal Python AST Optimizer

This is a project related to minifying or otherwise statically optimizing Python code. It can parse python to output a much smaller output with optionally excluded sections of code.

This project is an extension of the builtin ast module.

## Goals

The main reason I am making this is a compilation tool for another project I am working on. I wanted to be able to exclude code that goes into the final compiled solution, and this wanted to be able to remove classes/functions/etc from python by listing them and having a parser do all the checking. This project is built with that goal in mind; as is, it does not aim for perfectly minified python code, but extensibility and options around what gets excluded.

In the future I will aim to increase the accuracy of minification, but currently the focus remains on being able to exclude sections of code.
