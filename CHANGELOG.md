# Changelog

## [Unreleased]

## [9.0.0] - 2026-07-17

- [Deprecation] RegexNoMatchException renamed to RegexNoMatchError
- [Deprecation] Remove many modules that were never intended as public and resturcture entire project
- [Deprecation] Config completely restructured and location moved
- [Deprecation] Change vars_to_fold to name_or_attr_to_fold
- [Deprecation] Removed Config assume_this_machine, use name_or_attr_to_fold/calls_to_fold instead
- [Deprecation] Removed Config enums_to_fold, use name_or_attr_to_fold/calls_to_fold instead
- [Deprecation] Removed Config dict_keys_to_skip
- [Improvement] name_or_attr_to_fold now supports Attributes as well
- [Improvement] Default to not warning about not finding nodes to skip
- [Improvement] Ability to warn about names/attrs/calls to fold that were not found
- [Improvement] Keep making optimization passes if more optimizations may be available
- [Improvement] Minor performance optimizations in AST optimizer
- [Improvement] Make typing module public

## [8.2.3] - 2026-07-01

- [Fix] Weird case where unpacked values could be missing when dict_keys_to_skip are passed
- [Fix] MinifyUnparser how uses a Protocol since ast._Unparser was considered `Any`
- [Improvement] Optimization: Reduce superclass overhead

## [8.2.2] - 2026-06-22

- [Improvement] Optimization: Remove redundant visits of function ASTs

## [8.2.1] - 2026-06-21

- [Improvement] Folding function locals allows None values
- [Improvement] Additional optimization pass if function local was folded

## [8.2.0] - 2026-06-20

- [Improvement] Option to fold const int function locals

## [8.1.2] - 2026-06-01

- [Fix] Not respecting functions_safe_to_exclude_in_test_expr input
- [Improvement] Minor optimizations in minifier

## [8.1.1] - 2026-03-16

- [Improvement] Option to skip generics
- [Refactor] Base class for node transformers

## [8.1.0] - 2026-03-10

- [Improvement] Allow passing iterable of unused imports to ignore

## [8.0.2] - 2026-02-12

- [Improvement] Add missing cases for Is and IsNot in operation folding

## [8.0.1] - 2026-01-22

- [Improvement] Remove useless else nodes after if-return or if-raise

## [8.0.0] - 2026-01-19

- [Deprecation] Change location of simplify_named_tuples to OptimizationConfig
- [Deprecation] RegexReplacement defaults to 1
- [Deprecation] Restructure regex module paths

## [7.1.0] - 2026-01-18

- [Improvement] Option to change collection concat to unpack

## [7.0.0] - 2026-01-18

- [Deprecation] fold_constants now defaults to `False`
- [Deprecation] Force config args to be kwargs
- [Improvement] Option to remove typing cast

## [6.1.3] - 2026-01-17

- [Improvement] Combine If nodes where possible

## [6.1.2] - 2026-01-17

- [Improvement] No longer turn all type hints into int

## [6.1.1] - 2026-01-17

- [Improvement] Skipping `if ...: pass` when possible
- [Improvement] Change `while True:` to `while 1:`

## [6.1.0] - 2026-01-17

- [Improvement] Option to skip asserts

## [6.0.2] - 2026-01-17

- [Fix] Revert changes in 6.0.1
- [Improvement] NamedTuple with defaults can now be simplified

## [6.0.1] - 2026-01-16 [YANKED]

- [Improvement] Improvement NamedTuple detection

## [6.0.0] - 2026-01-16

- [Deprecation] skip_type_hints now accepts enum input instead of bool
- [Deprecation] "run_minify_parser" renamed to "run_unparser" and input order changed
- [Improvement] Option to skip all type hints (unsafe)
- [Improvement] Option to simplify NamedTuple to namedtuple

## [5.3.3] - 2026-01-14

- [Fix] Edge case with nested functions... again

## [5.3.2] - 2026-01-13

- [Improvement]  Skip useless try node

## [5.3.1] - 2026-01-12

- [Fix] Edge case with nested functions
- [Improvement] Add sys.platform to list of machine dependent attributes

## [5.3.0] - 2026-01-12

- [Deprecate] Remove warn_unusual_code config
- [Fix] Issue with constant folding when assignment is not constant

## [5.2.3] - 2025-12-22

- [Improvement] Update type hint for vars_to_fold

## [5.2.2] - 2025-12-21

- [Improvement] Minor performance optimization: Skip unneeded list recreation

## [5.2.1] - 2025-12-20

- [Improvement] Inline Global and Nonlocal nodes
- [Improvement] Minor performance optimizations in Minifier

## [5.2.0] - 2025-12-18

- [Deprecation] Remove NamesAndAttersDetector by merging it into UnusedImportSkipper
- [Improvement] Don't run UnusedImportSkipper if no imports

## [5.1.2] - 2025-12-17

- [Improvement] More accurate unused import detection

## [5.1.1] - 2025-12-17

- [Fix] Issue with broken imports and type hints in 5.1.0
- [Improvement] Option to remove unused imports and removal of autoflake dependency

## [5.1.0] - 2025-12-17 [YANKED]

- [Improvement] Option to remove unused imports and removal of autoflake dependency

## [5.0.3] - 2025-12-16

- [Improvement] Combine consecutive from imports

## [5.0.2] - 2025-12-13

- [Improvement] Combine consecutive imports

## [5.0.1] - 2025-12-13

- [Improvement] Expand operations that can be folded

## [5.0.0] - 2025-12-12

- [Deprecation] Remove "skip_name_equals_main" config, use vars_to_fold instead

## [4.0.0] - 2025-12-12

- [Deprecation] Renaming of config values
- [Improvement] Fold UnaryOp nodes

## [3.1.1] - 2025-12-07

- [Improvement] Add os.name to list of machine dependent attributes
- [Improvement] Remove dead If nodes

## [3.1.0] - 2025-12-07

- [Improvement] Support optimizations for current machine
- [Improvement] Fold Comparison nodes
- [Improvement] Remove dead If Expression nodes

## [3.0.1] - 2025-11-26

- [Improvement] Fold BoolOp nodes

## [3.0.0] - 2025-11-11

- [Deprecation] Minimum Python version increased to 3.11
- [Improvement] Support for folding enums

## [2.3.3] - 2025-08-24

- [Improvement] Remove duplicate slots entries

## [2.3.2] - 2025-08-16

- [Improvement] Inline AnnAssign nodes

## [2.3.1] - 2025-07-18

- [Fix] Revert changes from 2.2.2 since it might remove side effects

## [2.3.0] - 2025-07-12 [YANKED]

- [Improvement] Option to skip overload functions

## [2.2.2] - 2025-07-11 [YANKED]

- [Improvement] Remove if pass nodes

## [2.2.1] - 2025-07-11

- [Fix] Fix array out of bounds when parsing some functions

## [2.2.0] - 2025-06-22

- [Deprecation] Renaming of config values
- [Improvement] Fold BinOp nodes

## [2.1.2] - 2025-06-22

- [Improvement] Skip empty returns at the end of functions
- [Improvement] Better inlining check in minifier

## [2.1.1] - 2025-06-17

- [Improvement] Reduce excess whitespace in minifier

## [2.1.0] - 2025-06-12

- [Improvement] Allow module imports to be skipped

## [2.0.1] - 2025-06-11

- [Improvement] Variables to skip now also skips AugAssigns

## [2.0.0] - 2025-06-09

- [Deprecation] Break optimizations and minification into two separate classes

## [1.1.5] - 2025-05-25

- [Improvement] Skip writing redundant passes

## [1.1.4] - 2025-05-24

- [Improvement] Write break on the same line when able

## [1.1.3] - 2025-05-24

- [Improvement] Write semicolons after Assigns where able

## [1.1.2] - 2025-05-23

- [Improvement] Write continue and raise on the same line when able

## [1.1.1] - 2025-05-17

- [Improvement] Allow assigns to be written on the same line if they are the only line in that block

## [1.1.0] - 2025-05-15

- [Improvement] Allow passing int or str variables to fold. Assignment and imports of them will also be skipped

## [1.0.0] - 2025-05-14

- [Improvement] Initial release of code mostly ported from another project of time
