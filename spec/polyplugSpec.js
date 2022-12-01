/*
Tests for PolyPlug/
*/
describe("When working with PolyPlug,", function() {
    beforeEach(function() {
        // The object used for testing purposes.
        plug = polyplug();
    });

    describe("when serializing to or from the DOM,", function() {

      beforeEach(function() {
        // A fragment of HTML containing various generic elements we'll use to
        // exercise the code.
        node = document.createElement("div");
        node.setAttribute("id", "test-node");
        node.setAttribute("style", "font-weight: bold;");
        node.setAttribute("custom-attribute", "");
        node.innerHTML = `
        <p>Textual content.</p>
        <!-- A comment -->
        <form>
          <label for="testInput">Test Input</label>
          <input type="text" name="testInput" value="test"/>
          <textarea>Some free text content...</textarea>
          <input type="submit" value="Submit"/>
        </form>
        <ul id="list">
          <li>a</li>
          <li>b</li>
          <li>c</li>
        </ul>`;
        jsonString = `{
      "nodeType": 1,
      "tagName": "div",
      "attributes": {
        "id": "test-node",
        "style": "font-weight: bold;",
        "custom-attribute": ""
      },
      "childNodes": [
        {
          "nodeType": 1,
          "tagName": "p",
          "childNodes": [
            {
              "nodeType": 3,
              "nodeName": "#text",
              "nodeValue": "Textual content.",
              "childNodes": []
            }
          ]
        },
        {
          "nodeType": 8,
          "nodeName": "#comment",
          "nodeValue": " A comment ",
          "childNodes": []
        },
        {
          "nodeType": 1,
          "tagName": "form",
          "childNodes": [
            {
              "nodeType": 1,
              "tagName": "label",
              "attributes": {
                "for": "testInput"
              },
              "childNodes": [
                {
                  "nodeType": 3,
                  "nodeName": "#text",
                  "nodeValue": "Test Input",
                  "childNodes": []
                }
              ]
            },
            {
              "nodeType": 1,
              "tagName": "input",
              "attributes": {
                "type": "text",
                "name": "testInput",
                "value": "test"
              },
              "childNodes": []
            },
            {
              "nodeType": 1,
              "tagName": "textarea",
              "value": "Some free text content...",
              "childNodes": []
            },
            {
              "nodeType": 1,
              "tagName": "input",
              "attributes": {
                "type": "submit",
                "value": "Submit"
              },
              "childNodes": []
            }
          ]
        },
        {
          "nodeType": 1,
          "tagName": "ul",
          "attributes": {
            "id": "list"
          },
          "childNodes": [
            {
              "nodeType": 1,
              "tagName": "li",
              "childNodes": [
                {
                  "nodeType": 3,
                  "nodeName": "#text",
                  "nodeValue": "a",
                  "childNodes": []
                }
              ]
            },
            {
              "nodeType": 1,
              "tagName": "li",
              "childNodes": [
                {
                  "nodeType": 3,
                  "nodeName": "#text",
                  "nodeValue": "b",
                  "childNodes": []
                }
              ]
            },
            {
              "nodeType": 1,
              "tagName": "li",
              "childNodes": [
                {
                  "nodeType": 3,
                  "nodeName": "#text",
                  "nodeValue": "c",
                  "childNodes": []
                }
              ]
            }
          ]
        }
      ]
    }`;
      });

      describe("the toJSON function,", function() {
        it("takes an HTML node and returns an accurate string of JSON", function() {
          const result = plug.toJSON(node);
          // Ensure we get a string...
          expect(result).toBeInstanceOf(String);
          // that is valid JSON...
          const fromJSON = JSON.parse(result);
          // of the expected shape.
          const expectedObject = JSON.parse(jsonString);
          expect(fromJSON).toEqual(expectedObject);
        });
      });
      
      describe("the toDOM function,", function() {
        it("takes a JSON string and returns the expected DOM fragment", function() {
          const domResult = plug.toDOM(jsonString);
          // Because the JSON serialization removes extraneous things like
          // newlines (so the node object and domResult won't be the same), just
          // re-serialize to JSON to check they're the same.
          const jsonResult = plug.toJSON(domResult);
          const expectedObject = plug.toJSON(node);
          expect(jsonResult).toEqual(expectedObject);
        });
      });
    });
    describe("when mutating/patching nodes in the DOM tree,", function() {
      beforeEach(function() {
        // The old node to mutate.
        oldNode = document.createElement("div");
        oldNode.setAttribute("id", "test-node");
        oldNode.setAttribute("style", "font-weight: bold;");
        oldNode.setAttribute("old-custom-attribute", "");
        oldNode.innerHTML = `
        <p>Textual content.</p>
        <!-- A comment -->
        <form>
          <label for="testInput">Test Input</label>
          <input type="text" name="testInput" value="test"/>
          <textarea>Some free text content...</textarea>
          <input type="submit" value="Submit"/>
        </form>
        <ul id="list">
          <li id="a">a</li>
          <li id="b">b</li>
          <li id="c">c</li>
        </ul>`;
        // The new node used as the template to which to update.
        newNode = document.createElement("div");
        newNode.setAttribute("id", "test-node");
        // New font-weight value.
        newNode.setAttribute("style", "font-weight: normal;");
        // Remove old-custom-attribute.
        // Completely new-custom-attribute.
        newNode.setAttribute("new-custom-attribute", "");
        // Updated comment
        // Added id to form
        // Added new p node to form
        // Remove id from ul
        // Rearranged order of li
        newNode.innerHTML = `
        <p>Textual content.</p>
        <!-- A new comment -->
        <form id="new_form">
          <label for="testInput">Test Input</label>
          <input type="text" name="testInput" value="test"/>
          <textarea>Some free text content...</textarea>
          <p>Click button to submit.</p>
          <input type="submit" value="Submit"/>
        </form>
        <ul>
          <li id="c">c</li>
          <li id="b">b</li>
          <li id="a">a</li>
        </ul>`;
      });

      it("the oldNode is mutated to the newNode", function() {
        const expectedJSON = plug.toJSON(newNode);
        // The JSON serialization for both old and new are different.
        expect(plug.toJSON(oldNode)).not.toEqual(expectedJSON);
        // Mutate.
        const is_changed = plug.mutate(oldNode, newNode);
        // Confirmation the oldNode has changed.
        expect(is_changed).toEqual(true);
        // The JSON serialization for both old and new are now the same.
        expect(plug.toJSON(oldNode)).toEqual(expectedJSON);
      });

      it("the oldNode isn't changed if newNode is the same", function() {
        const expectedJSON = plug.toJSON(oldNode);
        const nodeA = plug.toDOM(expectedJSON);
        const nodeB = plug.toDOM(expectedJSON);
        // Mutate
        const is_changed = plug.mutate(nodeA, nodeB);
        // No change.
        expect(is_changed).toEqual(false);
      });
    });
    describe("when getting elements from the DOM,", function() {
      it("matching by id returns the expected element", function() {
        const result = plug.getElements({id: "testParaID"});
        expect(result.length).toEqual(1);
        expect(result[0].id).toEqual("testParaID");
        expect(result[0].tagName).toEqual("P");
      });
      it("an unmatched id returns an empty array", function() {
        const result = plug.getElements({id: "testParaIDFake"});
        expect(result.length).toEqual(0);
      });
      it("matching by tag returns the expected elements", function() {
        const result = plug.getElements({tag: "p"});
        expect(result.length).toEqual(2);
      });
      it("matching by class returns the expected elements", function() {
        const result = plug.getElements({classname: "testParaClass"});
        expect(result.length).toEqual(1);
        expect(result[0].className).toEqual("testParaClass");
      });
      it("matching by CSS selector returns the expected elements", function() {
        const result = plug.getElements({css: "p.testParaClass"});
        expect(result.length).toEqual(1);
        expect(result[0].className).toEqual("testParaClass");
      });
      it("non valid query returns null", function() {
        expect(plug.getElements({})).toEqual(null);
      });
    });
    describe("when registering events in the DOM,", function() {
      it("raises the expected polyplugSend event with the event context", function(done) {
        function eventListener(e) {
            const detail = JSON.parse(e.detail);
            expect(detail.type).toEqual("click");
            expect(detail.listener).toEqual("myTestClicker");
            expect(detail.target).toEqual({
              "nodeType": 1,
              "tagName": "button",
              "attributes": {
                "id": "testButton"
              },
              "childNodes": [
                {
                  "nodeType": 3,
                  "nodeName": "#text",
                  "nodeValue": "Click Me",
                  "childNodes": []
                }
              ]
            });
            done();
        }
        document.addEventListener("polyplugSend", eventListener);
        plug.registerEvent({id: "testButton"}, "click", "myTestClicker");
        const button = plug.getElements({id: "testButton"})[0];
        const clickEvent = new Event("click");
        button.dispatchEvent(clickEvent);
        document.removeEventListener("polyplugSend", eventListener);
      });
    });
    describe("when handling incoming messages,", function() {
      it("the updateDOM message calls the expected mutate", function() {
        const target = {
          "nodeType": 1,
          "tagName": "div",
          "attributes": {
            "id": "testMutate"
          },
          "childNodes": [
            {
              "nodeType": 1,
              "tagName": "h1",
              "attributes": {
                "class": "testClass"
              },
              "childNodes": [
                {
                  "nodeType": 3,
                  "nodeName": "#text",
                  "nodeValue": "This is a test, updated via morphing.",
                  "childNodes": []
                }
              ]
            }
          ]
        };
        const msg = JSON.stringify({
            type: "updateDOM",
            query: {
                id: "testMutate"
            },
            target: target
        });
        // Process the message.
        plug.receiveMessage(msg);
        // The DOM has been updated as expected.
        const updatedDIV = plug.getElements({id: "testMutate"})[0];
        const actual = plug.toJSON(updatedDIV);
        const expected = JSON.stringify(target);
        expect(actual).toEqual(expected);
      });
      it("the registerEvent message registers an event", function(done) {
        const msg = JSON.stringify({
            type: "registerEvent",
            query: {
                id: "testButton2"
            },
            eventType: "click",
            listener: "my_on_click_function"
        });
        plug.receiveMessage(msg);
        function eventListener(e) {
            const detail = JSON.parse(e.detail);
            expect(detail.type).toEqual("click");
            expect(detail.listener).toEqual("my_on_click_function");
            expect(detail.target).toEqual({
              "nodeType": 1,
              "tagName": "button",
              "attributes": {
                "id": "testButton2"
              },
              "childNodes": [
                {
                  "nodeType": 3,
                  "nodeName": "#text",
                  "nodeValue": "Click Me Again",
                  "childNodes": []
                }
              ]
            });
            done();
        }
        document.addEventListener("polyplugSend", eventListener);
        const button = plug.getElements({id: "testButton2"})[0];
        const clickEvent = new Event("click");
        button.dispatchEvent(clickEvent);
        document.removeEventListener("polyplugSend", eventListener);
      });
      it("the stdout message dispatches a polyplugStdout event", function(done) {
        function eventListener(e) {
            expect(e.detail).toEqual("Hello, world");
            done();
        }
        document.addEventListener("polyplugStdout", eventListener);
        const msg = JSON.stringify({
            type: "stdout",
            content: "Hello, world"
        });
        plug.receiveMessage(msg);
        document.removeEventListener("polyplugStdout", eventListener);
      });
      it("the stderr message dispatches a polyplugStdout event", function(done) {
        function eventListener(e) {
            expect(e.detail).toEqual("Hello, stderr");
            done();
        }
        document.addEventListener("polyplugStderr", eventListener);
        const msg = JSON.stringify({
            type: "stderr",
            content: "Hello, stderr"
        });
        plug.receiveMessage(msg);
        document.removeEventListener("polyplugStderr", eventListener);
      });
      it("the error message dispatches a polyplugErrorevent", function(done) {
        // Arbitrary error context from the remote interpreter.
        const errorContext = {
            exception: "ValueError",
            message: "The thing went bang!",
            stackTrace: ["frame1", "frame2", "frame3" ]
        }
        function eventListener(e) {
            expect(e.detail).toEqual(errorContext);
            done();
        }
        document.addEventListener("polyplugError", eventListener);
        const msg = JSON.stringify({
            type: "error",
            context: errorContext
        });
        plug.receiveMessage(msg);
        document.removeEventListener("polyplugError", eventListener);
      });
    });
});
