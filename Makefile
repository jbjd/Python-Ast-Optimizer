validate:
	ruff check .
	ruff format --check
	mypy .
	codespell personal_python_ast_optimizer tests setup.py README.md

test:
	coverage run --source=personal_python_ast_optimizer -m pytest
	@coverage report -m
