# PolyPlug 🦜🔌

PolyPlug is a browser based framework for linking the DOM and DOM based events
with scripting languages compiled to WASM.

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

Common tasks are scripted by a Makefile (tested on Linux):

```
$ make
There's no default Makefile target right now. Try:

make flake8 - run the flake8 Python checker.
make testjs - run the JavaScript test suite.
make testpy - run the Python test suite.
make minify - minify the project.
make tidy - Tidy the Python code with black.
```

## Running the tests

For the sake of simplicity (and familiarity) we use the
[Jasmine test framework](https://jasmine.github.io/index.html) to exercise the
JavaScript aspects of our code.

For similar reasons, we use [PyTest](https://pytest.org/) to exercise the
Pythonic aspects of our code.

## How it works

### JavaScript

Methods of the object returned by the `polyplug` function facilitate all
operations.

```JS
const plug = polyplug();
```

### Python

Flesh this out.
