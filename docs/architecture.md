# Architecture

PolyPlug is a relatively small implementation of a simple set of ideas. Since
the design of technology is often an exercise in trade-offs it's important to
explain PolyPlug's aims and objectives, so design decisions sit in a context.

PolyPlug is a framework for linking the DOM, DOM based events and perhaps
other aspects of the browser's capabilities with scripting languages compiled
to WASM.

It **is**:

* **Agnostic of interpreter**. There should be no need for bespoke modification
  of the interpreter so long as there is a way to capture `stdout` from the
  interpreter and have the interpreter evaluate code on-the-fly.
* **Message based**. Since web-workers have no access to the DOM and can only
  communicate with the main (UI) thread by sending via `postMessage()` and
  receiving via the `onmessage` event handler, a message based protocol is
  required. Because of the browser based context, messages are serialised with
  JSON.
* **Small**. On the web, size of asset matters as this directly influences how
  fast a page starts to work. "Small" also applies to the scope of PolyPlug so
  scope creep is avoided. PolyPlug should only concern itself with defining and
  handling a limited core set of messages upon which more complicated apps can
  be built. Since we might not cover everything due to "small-ness", perhaps
  some sort of plug-in system to allow bespoke / third party customisations and
  messages should be implemented?
* **Simple**. PolyPlug's code base is simple. If the code is easy to understand
  it's easier to spot bugs and maintain things as things mature. "Simple" also
  means it's easier for new contributors to learn the code and help.
* **Expressive**. This is always a work in progress, but the limited core set
  of messages that PolyPlug supports should elegantly and consistently provide
  as much capability as possible. In this way, the user is enabled to do many
  different things. What such capabilities are, and how they are expressed is
  more an aesthetic judgement, for which feedback is welcomed.

It is **NOT**:

* A Python/JavaScript broker. This is a non-trivial undertaking. It could be
  argued that it's better to keep these two "realms" separate (except via
  clearly defined messages), so unusual, unidiomatic and incoherent
  abstractions don't bleed into between the two programming worlds.
* A complete solution. If you want React or jQuery like capabilities for
  browser based app development, just go use React and jQuery. :-) Let many
  flowers bloom.
* Finished. Code is never finished and PolyPlug is written to be changed as
  and when the universe inevitably moves on.

## How it works

There are two pieces of code relating to PolyPlug:

* `polyplug.js` - JavaScript running in the main thread.
* `polyplug.py` - Python running in the interpreter (MicroPython, Pyodide
  etc...).

Depending on the implementation of PyScript, the interpreter may be running in
the main thread or in a web worker, and it is PyScript itself that acts as the
(trivial) broker between the two parts. An example implementation of this has
already been implemented in
[MicroPyScript](https://github.com/pyscript/micropyscript).

### JavaScript

Methods of the object returned by the `polyplug` function facilitate all
operations.

```JS
const plug = polyplug();
```

The resulting `plug` object essentially does five things:

1. Serialize and de-serialize nodes in the DOM to a JavaScript/JSON
   representation.
2. Mutate nodes in the DOM to a new state.
3. Reach into the DOM to reference specific nodes.
4. Register and coordinate (Python based) event handlers.
5. Use 1, 2, 3 and 4 to react to, and dispatch messages for, the Python
   interpreter.

The "normal" use case is for messages to be handled by the `plug` object (how
this works is explained below). But the functions relating to items 1, 2, 3 and
4 are made public as a courtesy and to aid testing.

The available functions are:

#### `plug.nodeToJS(node)`

Takes a node in the DOM and recursively converts it and its children into a
JSON encodable JavaScript object.

What information is captured?

* The nodeType (see: https://developer.mozilla.org/en-US/docs/Web/API/Node/nodeType).
* The tag or node name (e.g. "div", "p" or "input").
* The nodeValue (e.g. the textual content of a text node).
* An object containing the key/value pairs representing the attributes
  of a node.
* If a textarea, its "value" (i.e. textual content).
* An array of childNodes, also captured in the same way. Textarea does
  not have childNodes.

The nodeType is essential for representing the node with the correct "type"
when de-serialized.

#### `plug.jsToNode(obj)`

Takes a JavaScript object and returns the equivalent HTML node.

* The nodeType indicates what sort of element to create with the
  document object.
* The nodeValue indicates, for example, the textual content of a
  text node.
* Attributes, if appropriate, are added to the node.
* Child nodes are also recursively added, as appropriate.
* A textarea is a bit special, see the comments in-line for more
  information.

The resulting node should be merged into the DOM (rather than used to replace a
node). This ensures event handlers are retained.

#### `plug.mutate(oldNode, newNode)`

An unsophisticated DOM mutator.

Take an old HTML node and recursively mutate it to the new HTML node's
configuration.

Return a boolean indication to show if the mutation resulted in any
change to the old node.

#### `plug.getElements(q)`

Return a collection of HTML element[s] matching the query object "q", where
"q" looks like:

```JavaScript
q = {
  id: "someElementId"
};
```

In order of precedence, the function will try to find results by `id` or `tag`
or `classname` or `css` selector (but not a combination thereof).

If no matches found, returns `null`.

#### `plug.registerEvent(query, eventType, listener)`

Register an event listener, given:

* target element[s] via a query object (see getElements),
* the event type (e.g. "click"), and,
* the id of the listener to call in the remote interpreter.

The handler function is called by dispatching a polyplugSend event
with details of the event encoded as a JSON string.

Depending upon how the remote interpreter is run (on the main thread,
in a web worker, etc), this event should be handled to call the
expected function in the most appropriate way.

#### `plug.removeEvent(query, eventType, listener)`

Remove an event listener, given:

* target element[s] via a query object (see getElements),
* the event type (e.g. "click"), and,
* the id of the listener to call in the remote interpreter.

#### `plug.receriveMessage(raw)`

Receive a raw message string (containing JSON). Deserialize it and
dispatch the message to the appropriate handler function.

### Python

To register a function to handle DOM events in Python, use the `plug`
decorator:

```python
import arrr
from polyplug import plug, update, receive


@plug("#inputForm", "submit")
def handle_form(event):
  """
  Take the English input from the form, turn it into Pirate talk
  and update the DOM with the result.
  """
  english = event.target.find("#english").value
  pirate_text = arrr.translate(english)
  output = event.target.find("#output")
  output.innerHTML = f"{pirate_text}"
  update("#output", output)
```

## Message Protocol

To be finished off.

### Message Types

#### `updateDOM`

Handle messages from an interpreter to update the DOM.

Given a query to identify a target element, mutate it to the target state
(encoded as JSON).

Sample message:

```JavaScript
msg = {
  type: "updateDOM",
  query: {
    id: "idOfDomElementToMutate"
  },
  target: {
    ... JSON representation of the target state ...
  }
}
```

#### `registerEvent`

Handle requests from an interpreter to register an event listener.

Given a query to identify target element[s], listen for the event type
and handle with the referenced listener function in the remote
interpreter.

Sample message:

```javascript
msg = {
  type: "registerEvent",
  query: {
    id: "idOfDomElement"
  },
  eventType: "click",
  listener: "my_on_click_function_id"
}
```

#### `removeEvent`

Handle requests to unbind the referenced event type on the elements
matched by the query.

Sample message:

```JavaScript
msg = {
  type: "removeEvent",
  query: {
    id: "idOfDomElement"
  },
  eventType: "click",
}
```

#### `stdout`

Handle "normal" STDOUT output.

Simply dispatch a "polyplugStdout" custom event with the event's detail
containing the emitted characters.

Sample message:

```JavaScript
msg = {
  type: "stdout",
  content: "Some stuff to print to the terminal"
}
```

#### `stderr`

Handle "normal" STDERR output.

Simply dispatch a "polyplugStderr" custom event with the event's detail
containing the emitted characters.

Sample message:

```JavaScript
msg = {
  type: "stderr",
  content: "Some stuff from stderr"
}
```

#### `error`

Handle generic error conditions from the interpreter.

Dispatch a "polyplugError" custom event with the event detail set to
the error context.

Sample message:

```JavaScript
msg = {
  type: "error",
  context: {
    ... arbitrary data about the error condition ...
    (e.g. Exception name, line number, stack trace etc)
  }
}
```
