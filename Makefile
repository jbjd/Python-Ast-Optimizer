validate:
	ruff check .
	ruff format --check
	mypy . --check-untyped-defs
	codespell personal_python_ast_optimizer tests setup.py README.md

test:
	pytest --cov=personal_python_ast_optimizer --cov-report term-missing
