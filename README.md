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

That is all.

## Developer setup

Common tasks are scripted by a Makefile (tested on Linux):

```
$ make
There's no default Makefile target right now. Try:

make minify - minify the source.
make test - run the test suite.
```

## Running the tests

For the sake of simplicity (and familiarity) we use the
[Jasmine test framework](https://jasmine.github.io/index.html) to exercise the
JavaScript aspects of our code.

## How it works

Methods of the object returned by the `polyplug` function facilitate all
operations.

```JS
const plug = polyplug();
```

Flesh this out.
