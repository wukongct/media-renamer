.PHONY: help env clean run test lint doc

VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON=${VENV_NAME}/bin/python3

.DEFAULT: help
help:
	@echo "make env"
	@echo "    prepare virtual environment"
	@echo "make clean"
	@3cho "    remove existing environment"
	@echo "make run"
	@echo "    run project"
	@echo "make test"
	@echo "    run tests"
	@echo "make lint"
	@echo "    run pylint and mypy"
	@echo "make doc"
	@echo "    build sphinx documentation"

env: $(VENV_NAME)/bin/activate
$(VENV_NAME)/bin/activate: requirements.txt
	test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	${PYTHON} -m pip install -r requirements.txt
	touch $(VENV_NAME)/bin/activate

clean:
	rm -rf $(VENV_NAME)

