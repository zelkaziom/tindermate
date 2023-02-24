
black:
	time black .

black-check:
	time black . --check

mypy:
	time mypy .

ruff:
	time ruff . --fix

ruff-check:
	time ruff .

all-lint: black mypy ruff
all-lint-check: black-check mypy ruff-check

.PHONY: black black-check mypy ruff ruff-check all-lint all-lint-check
