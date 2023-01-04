# PolyPlug 🦜🔌

PolyPlug is a browser based framework for linking the DOM and DOM based events
with scripting languages compiled to WASM.

For more information [please read our documentation](https://polyplug.readthedocs.io/en/latest/) (the source for which is in the `./docs` directory).

It is:

* Agnostic of the interpreter receiving and responding to DOM events.
* Message based (JSON).
* Small (efficient to start).
* Simple (easier to maintain).
* Expressive (capable of many things).

This is the way:

* Obvious code.
* Simple is good.
* No dependencies.
* Vanilla JavaScript.
* Comments.
* Tests.
* Build for change.

This project was created for research purposes as part of the efforts to build
[PyScript](https://pyscript.net).

There are two sides to PolyPlug:

* The `polyplug.js` code to be run in the main thread of the browser.
* Code, to be run in the interpreter of the scripting language, to communicate
  with PolyPlug. Currently only `polyplug.py` exists as a reference
  implementation.

That is all.

## Developer setup

For Python development, create a new virtual environment and install the
required packages:

```
$ pip install -r requirements.txt
```

For JavaScript development, just edit the file and run the tests. _There are
deliberately no dependencies or complex tooling to ensure simplicity_. Should
you wish to minify the JavaScript source, you can (optionally) install
[uglifyjs](https://github.com/mishoo/UglifyJS).

Common tasks are scripted by a Makefile (tested on Linux and Mac):

```
$ make
There's no default Makefile target right now. Try:

make flake8 - run the flake8 Python checker.
make testjs - run the JavaScript test suite.
make testpy - run the Python test suite.
make minify - minify the project.
make tidy - tidy the Python code with black.
make docs - use Sphinx to create project documentation.
```

## Running the tests

For the sake of simplicity (and familiarity) we use the
[Jasmine test framework](https://jasmine.github.io/index.html) to exercise the
JavaScript aspects of our code.

For similar reasons, we use [PyTest](https://pytest.org/) to exercise the
Pythonic aspects of our code.
