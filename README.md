# Personal Python AST Optimizer

This is a project related to minifying or otherwise statically optimizing Python code. It can parse python to yield a much smaller output with optionally excluded sections of code.

## Goals

The main reason I am making this is a compilation tool for another project I am working on. I wanted to be able to exclude code that goes into the final compiled solution, and this wanted to be able to remove classes/functions/etc from my dependencies that I know are unused. This then expanded to adding dead code elimination and other performance optimizations.
