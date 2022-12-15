SHELL := /bin/bash

all:
	@echo "There's no default Makefile target right now. Try:"
	@echo ""
	@echo "make flake8 - run the flake8 Python checker."
	@echo "make testjs - run the JavaScript test suite."
	@echo "make testpy - run the Python test suite."
	@echo "make minify - minify the project."
	@echo "make tidy - Tidy the Python code with black."

flake8:
	flake8 .

testjs:
	python -m webbrowser "SpecRunner.html"

testpy:
	pytest -v --random-order --cov-report term-missing --cov=polyplug tests/

minify:
	uglifyjs polyplug.js --compress --mangle -o polyplug.min.js

tidy:
	black -l 79 .
