
black:
	black .

black-check:
	black . --check

mypy:
	mypy .

ruff:
	ruff . --fix

ruff-check:
	ruff .

all-lint: black mypy ruff
all-lint-check: black-check mypy ruff-check

.PHONY: black black-check mypy ruff ruff-check all-lint all-lint-check
