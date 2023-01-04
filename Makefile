SHELL := /bin/bash

all:
	@echo "There's no default Makefile target right now. Try:"
	@echo ""
	@echo "make flake8 - run the flake8 Python checker."
	@echo "make testjs - run the JavaScript test suite."
	@echo "make testpy - run the Python test suite."
	@echo "make minify - minify the project."
	@echo "make tidy - tidy the Python code with black."
	@echo "make docs - use Sphinx to create project documentation."

clean:
	rm -rf .coverage
	rm -rf .pytest_cache
	rm -rf docs/_build
	find . \( -name '*.py[co]' -o -name dropin.cache \) -delete
	find . | grep -E "(__pycache__)" | xargs rm -rf

flake8:
	flake8 .

testjs:
	python -m webbrowser "SpecRunner.html"

testpy: clean
	pytest -v --random-order --cov-report term-missing --cov=polyplug tests/

minify:
	uglifyjs polyplug.js --compress --mangle -o polyplug.min.js

tidy:
	black -l 79 .

docs: clean
	$(MAKE) -C docs html
	@echo "Documentation can be found here:"
	@echo file://`pwd`/docs/_build/html/index.html
	@echo ""
