validate:
	ruff check .
	ruff format --check
	mypy .
	codespell personal_python_ast_optimizer tests setup.py README.md

override PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD

test:
	coverage run --source=personal_python_ast_optimizer -m pytest
	@coverage report -m
