SHELL := /bin/bash

all:
	@echo "There's no default Makefile target right now. Try:"
	@echo ""
	@echo "make test - while serving the app, run the test suite in browser."
	@echo "make minify - minify the project."

test:
	python -m webbrowser "SpecRunner.html"

minify:
	uglifyjs polyplug.js --compress --mangle -o polyplug.min.js
