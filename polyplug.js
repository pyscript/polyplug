"use strict";
/******************************************************************************
PolyPlug 🦜🔌

A framework for linking the DOM and DOM based events with scripting languages
compiled to WASM. Part of the PyScript project.

See the README for more details, design decisions, and an explanation of how
things work.

This code does essentially five things:

1. Serialize and de-serialize nodes in the DOM via JSON.
2. Mutate nodes in the DOM to a new state.
3. Reach into the DOM to reference specific nodes.
4. Register and coordinate (remote) event handlers.
5. Use 1, 2, 3 and 4 while interacting, via message passing, with a scripting
   language.

Authors:
- Nicholas H.Tollervey (ntollervey@anaconda.org)

Copyright (c) 2022 Anaconda Inc. 

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
******************************************************************************/

const polyplug = function() {

    /**************************************************************************
    Internal state for PolyPlug.
    **************************************************************************/

    // Tracks event handler functions.
    const REGISTERED_EVENTS = {};

    /**************************************************************************
    Serialization functions for PolyPlug.
    **************************************************************************/

    function nodeToJS(node) {
        /*
        Takes a node in the DOM and recursively converts it and its children
        into a JSON encodable JavaScript object.

        What information is captured?

        * The nodeType (see: https://developer.mozilla.org/en-US/docs/Web/API/Node/nodeType).
        * The tag or node name (e.g. "div", "p" or "input").
        * The nodeValue (e.g. the textual content of a text node).
        * An object containing the key/value pairs representing the attributes
          of a node.
        * If a textarea, its "value" (i.e. textual content).
        * An array of childNodes, also captured in the same way. Textarea does
          not have childNodes.

        The nodeType is essential for representing the node with the correct
        "type" when de-serialized.
        */
        const obj = {
            nodeType: node.nodeType
        };
        if (node.tagName) {
            obj.tagName = node.tagName.toLowerCase();
        } else if (node.nodeName) {
            obj.nodeName = node.nodeName;
        }
        if (node.nodeValue) {
            obj.nodeValue = node.nodeValue;
        }
        const attrs = {};
        if (node.attributes && node.attributes.length > 0) {
            for (let i=0; i<node.attributes.length; i++) {
                attrs[node.attributes[i].nodeName] = node.attributes[i].nodeValue;
            }
        }
        if (Object.keys(attrs).length > 0) {
            obj.attributes = attrs;
        }
        if (obj.tagName === "textarea") {
            obj.value = node.value;
        }
        const childNodes = node.childNodes;
        const childNodesJS = [];
        // textarea nodes are special, in that they shouldn't have childNodes
        // since their content is supposed to be defined via their "value".
        if (obj.tagName !== 'textarea' && childNodes && childNodes.length > 0) {
            for (let i=0; i<childNodes.length; i++) {
                const child = nodeToJS(childNodes[i]);
                if (!(child.nodeValue && child.nodeValue.trim() === "")) {
                    childNodesJS.push(child);
                }
            }
        }
        obj.childNodes = childNodesJS;
        return obj;
    }

    function jsToNode(obj) {
        /*
        Takes a JavaScript object and returns the equivalent HTML node.

        * The nodeType indicates what sort of element to create with the
          document object.
        * The nodeValue indicates, for example, the textual content of a
          text node.
        * Attributes, if appropriate, are added to the node.
        * Child nodes are also recursively added, as appropriate.
        * A textarea is a bit special, see the comments in-line for more
          information.

        The resulting node should be merged into the DOM (rather than used to
        replace a node). This ensures event handlers are retained.
        */
        let node = null;  // The eventual result. 
        // See: https://developer.mozilla.org/en-US/docs/Web/API/Node/nodeType
        switch (obj.nodeType) {
            // ELEMENT_NODE
            case 1: {
                node = document.createElement(obj.tagName);
                if (obj.attributes && Object.keys(obj.attributes).length > 0) {
                    Object.entries(obj.attributes).map(attribute => {
                        node.setAttribute(attribute[0], attribute[1]);
                    })
                }
                if (obj.tagName === "textarea") {
                    node.value = obj.value;
                }
                break;
            }
            // TEXT_NODE
            case 3: {
                return document.createTextNode(obj.nodeValue);
            }
            // COMMENT_NODE
            case 8: {
                return document.createComment(obj.nodeValue);
            }
            // DOCUMENT_FRAGMENT_NODE
            case 11: {
                node = document.createDocumentFragment();
                break;
            }
            default: {
                // Default to an empty fragment node.
                return document.createDocumentFragment();
            }
        }
        // Recursively recreate the child nodes.
        // (textarea nodes are special, in that they shouldn't have childNodes
        // since their content is supposed to be defined via their "value".)
        if (obj.tagName !== 'textarea' && obj.childNodes && obj.childNodes.length > 0) {
            for (const childNode of obj.childNodes) {
                node.appendChild(jsToNode(childNode));
            }
        }
        return node;
    }

    /**************************************************************************
    DOM mutation functions for PolyPlug.
    **************************************************************************/

    function patch(oldNode, newNode) {
        /*
        Take an old HTML node and recursively patch its children with the new
        HTML node's children.

        Return a boolean indication if the patch resulted in any change to the
        old node.
        */
        let oldChild = oldNode.firstChild;  // current oldChild node.
        let newChild = newNode.firstChild;  // equivalent newChild node.
        let oldNextChild;  // to reference the next "old" node.
        let newNextChild;  // to reference the next equivalent "new" node.
        let changed = false;  // flag to indicate change to oldNode.

        // Handle pairs of equivalent old/new nodes.
        while (oldChild != null && newChild != null) {
            // Update references to the next nodes to handle after the
            // current ones.
            oldNextChild = oldChild.nextSibling;
            newNextChild = newChild.nextSibling;
            if(oldChild.nodeType !== newChild.nodeType || oldChild.nodeName !== newChild.nodeName) {
                // The old and new child nodes are completely different. Just
                // replace old with new.
                changed = true;
                oldNode.replaceChild(newChild, oldChild)
            } else if (oldChild.nodeType === oldChild.TEXT_NODE || oldChild.nodeType === oldChild.COMMENT_NODE) {
                // Check if textual content of TEXT_NODEs or COMMENT_NODEs
                // needs updating.
                if (oldChild.nodeValue !== newChild.nodeValue) {
                    changed = true;
                    oldChild.nodeValue = newChild.nodeValue;
                }
            } else {
                // In all other cases, patch the attributes and recurse into
                // the branches of the DOM tree.
                changed = patchAttrs(oldChild, newChild) || changed;
                changed = patch(oldChild, newChild) || changed;
            }
            // Swap to next nodes. Rinse and repeat. ;-)
            oldChild = oldNextChild;
            newChild = newNextChild;
        }
        if (newChild) {
            // Handle a "spare" newChild node that doesn't have an oldChild
            // equivalent to patch.
            do {
                // Just keep adding the spare newChild nodes to the oldNode
                // parent.
                changed = true;
                newNextChild = newChild.nextSibling;
                oldNode.appendChild(newChild);
                // Swap, rinse, repeat.
                newChild = newNextChild;
            } while (newChild);
        }
        if (oldChild) {
            // Handle a "spare" oldChild node that doesn't have a newChild
            // equivalent. I.e. the oldChild is to be removed.
            do {
                // Just keep removing the spare oldChild nodes from the oldNode
                // parent.
                changed = true;
                oldNextChild = oldChild.nextSibling;
                oldNode.removeChild(oldChild)
                // Swap, rinse, repeat.
                oldChild = oldNextChild;
            } while (oldChild);
        }
        // Return if the oldNode has changed as a result of the patch.
        return changed;
    }

    function patchAttrs(oldNode, newNode) {
        /*
        Takes an old node and updates its attributes to those from the new
        node.

        Return a boolean indication if any of the attributes have actually
        changed as a result of the patch.
        */
        let changed = false;

        // Check for changes in attributes that already exist for the old node.
        let i = 0;
        if (oldNode.attributes) {
            i = oldNode.attributes.length;
            while (i--) {
                const oldAttr = oldNode.attributes[i];
                const newAttr = newNode.attributes[oldAttr.name];
                if (newAttr == null) {
                    // Remove the attribute, it doesn't exist on the newNode.
                    changed = true;
                    oldNode.removeAttribute(oldAttr.name);
                } else if (oldAttr.nodeValue !== newAttr.nodeValue) {
                    // Attribute's value needs updating to newNode's.
                    changed = true;
                    oldAttr.nodeValue = newAttr.nodeValue;
                }
            }
        }
        // Check for new attributes to add to the old node.
        if (newNode.attributes) {
            i = newNode.attributes.length;
            while (i--) {
                const {name, nodeValue} = newNode.attributes[i];
                // Ignore attributes that already exist on oldNode.
                if (!oldNode.hasAttribute(name)) {
                    changed = true;
                    oldNode.setAttribute(name, nodeValue);
                }
            }
        }
        // Return if the oldNode's attributes have actually changed as a
        // result of the patch.
        return changed;
    }

    function mutate(oldNode, newNode) {
        /*
        An unsophisticated DOM mutator.

        Take an old HTML node and recursively mutate it to the new HTML node's
        configuration.

        Return a boolean indication to show if the mutation resulted in any
        change to the old node.
        */
        const changed = patchAttrs(oldNode, newNode)
        return patch(oldNode, newNode) || changed;
    }

    /**************************************************************************
    DOM reference functions for PolyPlug.
    **************************************************************************/

    function getElements(q) {
        /*
        Return a collection of HTML element[s] matching the query object "q".

        In order of precedence, the function will try to find results by id or
        tag or classname or CSS selector (but not a combination thereof).

        If no matches found, returns null.
        */
        if (q.id) {
            // getElementById doesn't return a collection, hence wrapping the
            // result as an array, for the sake of consistency.
            const result = [];
            const element = document.getElementById(q.id);
            if (element) {
                result.push(element);
            }
            return result;
        } else if (q.tag) {
            return document.getElementsByTagName(q.tag);
        } else if (q.classname) {
            return document.getElementsByClassName(q.classname);
        } else if (q.css) {
            return document.querySelectorAll(q.css);
        }
        return null;  // Explicit > implicit. ;-)
    }

    /**************************************************************************
    Event handling functions for PolyPlug.
    **************************************************************************/

    function registerEvent(query, eventType, listener) {
        /*
        Register an event listener, given:

        * target element[s] via a query object (see getElements),
        * the event type (e.g. "click"), and,
        * the name of the listener to call in the remote interpreter.

        The handler function is called by dispatching a polyplugSend event
        with details of the event encoded as a JSON string.

        Depending upon how the remote interpreter is run (on the main thread,
        in a web worker, etc), this event should be handled to call the
        expected function in the most appropriate way.
        */
        const elements = getElements(query);
        const eventHandler = function(e) {
            const detail = JSON.stringify({
                type: e.type,
                target: nodeToJS(e.target),
                listener: listener
            });
            const send = new CustomEvent("polyplugSend", {detail: detail});
            document.dispatchEvent(send);
        }
        REGISTERED_EVENTS[listener] = eventHandler;
        elements.forEach(function(element) {
            element.addEventListener(eventType, eventHandler);
        });
    }

    function removeEvent(query, eventType, listener) {
        /*
        Remove an event listener, given:

        * target element[s] via a query object (see getElements),
        * the event type (e.g. "click"), and,
        * the name of the listener to call in the remote interpreter.
        */
        const elements = getElements(query);
        const eventHandler = REGISTERED_EVENTS[listener];
        if (eventHandler) {
            elements.forEach(function(element) {
                element.removeEventListener(eventType, eventHandler);
            });
            delete REGISTERED_EVENTS[listener];
        }
    }

    /**************************************************************************
    Message handling functions for PolyPlug.
    **************************************************************************/

    function receiveMessage(raw) {
        /*
        Receive a raw message string (containing JSON). Deserialize it and
        dispatch the message to the appropriate handler function.
        */
        try {
            const message = JSON.parse(raw);
            switch (message.type) {
                case "updateDOM":
                    onUpdateDOM(message);
                    break;
                case "registerEvent":
                    onRegisterEvent(message);
                    break;
                case "removeEvent":
                    onRemoveEvent(message);
                    break
                case "stdout":
                    onStdout(message);
                    break;
                case "stderr":
                    onStderr(message);
                    break;
                case "error":
                    onError(message);
                    break;
                default:
                    console.log("Unknown message type.")
                    console.log(message)
                    break;
            }
        } catch (error) {
            onError(error);
        }
    }

    function onUpdateDOM(msg) {
        /*
        Handle messages from an interpreter to update the DOM.

        Given a query to identify a target element, mutate it to the target
        state (encoded as JSON).

        Sample message:

        msg = {
            type: "updateDOM",
            query: {
              id: "idOfDomElementToMutate"
            },
            target: {
                ... JSON representation of the target state ...
            }
        }
        */
        const elements = getElements(msg.query);
        if (elements.length === 1) {
            // Update the single valid match to 
            const oldElement = elements[0];
            const newElement = jsToNode(msg.target)
            mutate(oldElement, newElement);
        }
    }

    function onRegisterEvent(msg) {
        /*
        Handle requests from an interpreter to register an event listener.

        Given a query to identify target element[s], listen for the event type
        and handle with the referenced listener function in the remote
        interpreter.

        Sample message:

        msg = {
            type: "registerEvent",
            query: {
                id: "idOfDomElement"
            },
            eventType: "click",
            listener: "my_on_click_function"
        }
        */
        registerEvent(msg.query, msg.eventType, msg.listener);
    }

    function onRemoveEvent(msg) {
        /*
        Handle requests to unbind the referenced event type on the elements
        matched by the query.

        Sample message:

        msg = {
            type: "removeEvent",
            query: {
                id: "idOfDomElement"
            },
            eventType: "click",
        }
        */
        removeEvent(msg.query, msg.eventType);
    }

    function onStdout(msg) {
        /*
        Handle "normal" STDOUT output.

        Simply dispatch a "polyplugStdout" custom event with the event's detail
        containing the emitted characters.

        Sample message:

        msg = {
            type: "stdout",
            content: "Some stuff to print to the terminal"
        }
        */
        const polyplugStdout = new CustomEvent("polyplugStdout", {detail: msg.content});
        document.dispatchEvent(polyplugStdout);
    }

    function onStderr(msg) {
        /*
        Handle "normal" STDERR output.

        Simply dispatch a "polyplugStderr" custom event with the event's detail
        containing the emitted characters.

        Sample message:

        msg = {
            type: "stderr",
            content: "Some stuff from stderr"
        }
        */
        const polyplugStderr = new CustomEvent("polyplugStderr", {detail: msg.content});
        document.dispatchEvent(polyplugStderr);
    }

    function onError(msg) {
        /*
        Handle generic error conditions from the interpreter.

        Dispatch a "polyplugError" custom event with the event detail set to
        the error context.

        Sample message:

        msg = {
            type: "error",
            context: {
                ... arbitrary data about the error condition ...
                (e.g. Exception name, line number, stack trace etc)
            }
        }
        */
        const polyplugError = new CustomEvent("polyplugError", {detail: msg.context});
        document.dispatchEvent(polyplugError);
    }

    return {
        nodeToJS: nodeToJS,
        jsToNode: jsToNode,
        mutate: mutate,
        getElements: getElements,
        registerEvent: registerEvent,
        removeEvent: removeEvent,
        receiveMessage: receiveMessage
    }
};
