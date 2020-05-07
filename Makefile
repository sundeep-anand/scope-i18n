
.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

.PHONY: deps
deps:
	pip3 install -r requirements.txt

.PHONY: web
web:
	python3 manage.py runserver

.PHONY: envinfo
envinfo:
	uname -a
	pip list

.PHONY: lint
lint:
	flake8 --ignore=E501,E722,F401,F403,F405,F841,W504 web cli src
