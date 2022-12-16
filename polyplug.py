import binascii
import builtins
import hashlib
import json


# Registered event listeners.
LISTENERS = {}


class Query:
    """
    Encapsulates a query to match elements in the DOM.

    A query must have one, and only one, of:

    * id - a unique element id (e.g. "myElementId").
    * classname - a class (e.g. "my-css-class").
    * tag - a tag name (e.g. "p").
    * css - a css selector (e.g "p.className").

    These types of query relate to the four ways in which elements in an HTML
    document may be identified.

    A Query is instantiated with a string using the following common syntax
    for identifying the different types of query:

    * #id-name - Starting with a hash indicates an element's unique id.
    * .class-name - Starting with a full stop indicates a CSS class name.
    * p - A string of only alphabetical characters is treated as a tag name.
    * p.classname - Anything else is assumed to be a css selector.

    E.g.

    q = Query(".myElementID")
    """

    def __init__(self, query):
        """
        Validate and interpret the query string.
        """
        self.raw_query = query
        target = None
        if query[:1] == "#":
            # Unique id.
            target = query[1:]
            if target:
                self.query_type = "id"
            else:
                raise ValueError("Invalid id.")
        elif query[:1] == ".":
            # CSS class.
            target = query[1:]
            if target:
                self.query_type = "classname"
            else:
                raise ValueError("Invalid class.")
        elif query.isalpha():
            # tagName.
            target = query
            self.query_type = "tag"
        else:
            # CSS selector.
            target = query
            self.query_type = "css"

        if target:
            setattr(self, self.query_type, target)
        else:
            raise ValueError("Bad query specification.")

    @property
    def as_dict(self):
        """
        Return a dict to be JSON encoded.
        """
        return {
            self.query_type: getattr(self, self.query_type),
        }


class DomEvent:
    """
    Represents an event dispatched in the DOM.

    The event_type (e.g. "click") and target (DOM element that was the source
    of the event) are referenced.
    """

    def __init__(self, event_type, target):
        self.event_type = event_type
        self.target = target


class HTMLTokenizer:
    """
    Turns a string into a structured representation of the DOM.

    MUST USE XHTML (i.e. open and closing tags).
    """

    QUOTES = "\"'"

    def __init__(self, raw):
        self.raw = raw
        self.len = len(raw)
        self.pos = 0
        self.char = self.next_char()

    def next_char(self):
        """
        Get the next character, or return an empty string for EOF or no raw
        input.
        """
        if self.len and self.pos < self.len:
            self.char = self.raw[self.pos]
            self.pos += 1
            return self.char
        else:
            self.char = ""
        return ""

    def get_char(self):
        """
        Get the current character, and step to the next one.
        """
        result = self.char
        self.next_char()
        return result

    def skip_ws(self):
        """
        Skip over whitespace.
        """
        while self.char.isspace():
            self.next_char()

    def match(self, expected):
        """
        Return a boolean indication if the next character[s] is the expected
        character.

        Expected could be a multi-character match (mainly used for single and
        double quotes). E.g. expected = "\"'"
        """
        self.skip_ws()
        if self.char in expected:
            self.next_char()
            return True
        return False

    def expect(self, expected):
        """
        Raise an exception if the expected character[s] is not matched.
        """
        if not self.match(expected):
            raise ValueError("Bad HTML syntax.")

    def get_name(self):
        """
        Get the name of a tag or attribute.

        E.g. used to extract "div" and "id" from this fragment:

        <div id="foo">
        """
        self.skip_ws()
        result = ""
        while True:
            c = self.char
            if not (c.isalpha() or c.isdigit() or c in "_-."):
                break
            result += self.get_char()
        return result

    def get_value(self):
        """
        Get the value associated with an attribute.

        E.g. used to extract the "foo" value (without quotes) from this
        fragment:

        <div id="foo">
        """
        self.skip_ws()
        result = ""
        try:
            self.expect("=")
            self.expect(self.QUOTES)
            while True:
                c = self.char
                if not (c.isalpha() or c.isdigit() or c in "_-. ;:!"):
                    break
                result += self.get_char()
            self.expect(self.QUOTES)
            return result
        except ValueError:
            return ""

    def get_attrs(self):
        """
        Return an Attributes instance representing any attributes attached to
        an ElementTag.
        """
        attrs = Attributes()
        name = self.get_name()
        while name:
            value = self.get_value()
            attrs[name] = value
            name = self.get_name()
        return attrs

    def get_text(self, until="<"):
        """
        Return textual content until the start of a new Node ("<") or until
        "until" matches.
        """
        result = ""
        until_len = len(until)
        while result[-until_len:] != until and self.char:
            result += self.get_char()
        if result[-until_len:] == until:
            self.pos = self.pos - until_len
            if self.char:
                self.pos = self.pos - 1
            self.next_char()
            return result[:-until_len]
        else:
            # EOF
            return result

    def tokenize(self, parent=None):
        """
        Tokenize the raw HTML input and return a DOM representation using the
        Node and Attributes classes defined below.

        The parent ElementNode is given since we're always parsing its
        innerHTML.
        """
        if not isinstance(parent, ElementNode):
            raise ValueError("Parent must be an ElementNode")
        current_node = None
        current_parent = parent
        while self.char:
            if self.match("<"):
                # Tag opens.
                if self.match("/"):
                    # End tag. Close and check depth of tree.
                    # Get the name of the closing tag.
                    name = self.get_name()
                    if current_node and name == current_node.tagName:
                        # Close current node and continue at current depth.
                        current_parent.add_child(current_node)
                        current_node = None
                    elif name == current_parent.tagName:
                        # Step back up the tree to the parent context.
                        current_node = current_parent
                        current_parent = current_node.parent
                        current_parent.add_child(current_node)
                        current_node = None
                    else:
                        # Unexpected close tag.
                        raise ValueError("Unexpected close tag.", name)
                    self.expect(">")
                elif self.match("?"):
                    # XML prolog - consume and ignore.
                    self.get_attrs()
                    self.expect("?")
                    self.expect(">")
                elif self.match("!"):
                    # CommentNode - get nodeValue.
                    self.expect("-")
                    self.expect("-")
                    value = ""
                    while True:
                        value += self.get_char()
                        if value[-3:] == "-->":
                            break
                    comment = CommentNode(nodeValue=value[:-3])
                    current_parent.add_child(comment)
                else:
                    # ElementNode
                    tagName = self.get_name()
                    attrs = self.get_attrs()
                    if current_node:
                        current_parent = current_node
                    if tagName == "textarea":
                        self.expect(">")
                        value = self.get_text(until="</textarea>")
                        textarea_node = ElementNode(
                            tagName=tagName,
                            attributes=attrs,
                            value=value,
                            parent=current_parent,
                        )
                        for c in "</textarea>":
                            self.expect(c)
                        current_parent.add_child(textarea_node)
                    else:
                        current_node = ElementNode(
                            tagName=tagName,
                            attributes=attrs,
                            parent=current_parent,
                        )
                        self.expect(">")
            else:
                # TextNode
                value = self.get_text()
                text = TextNode(nodeValue=value)
                if current_node:
                    current_node.add_child(text)
                else:
                    current_parent.add_child(text)


class Node:
    """
    Represents a node in the DOM.
    """

    def __init__(self, **kwargs):
        self._node = kwargs
        self.parent = kwargs.get("parent")

    @property
    def outerHTML(self):
        """
        Get a string representation of the element's outer HTML.
        """
        return NotImplemented

    @property
    def as_dict(self):
        """
        JSON serializable.
        """
        return NotImplemented


class Attributes(dict):
    """
    Represents a collection of attributes attached to an ElementNode.
    """

    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            raise AttributeError("No such attribute: " + key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        if key in self:
            del self[key]
        else:
            raise AttributeError("No such attribute: " + key)


class ElementNode(Node):
    """
    An element defined by a tag, may have attributes and children.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tagName = kwargs["tagName"]
        self.attributes = Attributes(kwargs.get("attributes", {}))
        if self.tagName == "textarea":
            # The textarea doesn't have children. Only a text value.
            self.value = kwargs.get("value", "")

    def add_child(self, child):
        """
        Add a child node to the children of this node.
        """
        children = self._node.get("childNodes", [])
        node_dict = child
        if isinstance(child, Node):
            node_dict = child.as_dict
        node_dict["parent"] = self
        children.append(node_dict)
        self._node["childNodes"] = children

    @property
    def outerHTML(self):
        """
        Get a string representation of the element's outer HTML.
        """
        result = "<" + self.tagName
        for attr, val in self.attributes.items():
            result += " " + attr + '="' + val + '"'
        result += ">"
        if self.tagName == "textarea":
            result += self.value
        else:
            result += self.innerHTML
        result += "</" + self.tagName + ">"
        return result

    @property
    def innerHTML(self):
        """
        Get a string representation of the element's inner HTML.
        """
        result = ""
        for child in self.childNodes:
            result += child.outerHTML
        return result

    @innerHTML.setter
    def innerHTML(self, raw):
        """
        Use the raw innerHTML to create children.
        """
        self._node["childNodes"] = []
        tok = HTMLTokenizer(raw)
        tok.tokenize(self)

    @property
    def childNodes(self):
        """
        A data structure representing the tree of child nodes.
        """
        if self.tagName == "textarea":
            # The textarea doesn't have children. Only a text value.
            return []
        else:
            children = self._node.get("childNodes", [])
            result = []
            for child in children:
                node_type = child.get("nodeType")
                child["parent"] = self
                if node_type == 1:
                    # ELEMENT_NODE
                    result.append(ElementNode(**child))
                elif node_type == 3:
                    # TEXT_NODE
                    result.append(TextNode(**child))
                elif node_type == 8:
                    # COMMENT_NODE
                    result.append(CommentNode(**child))
                else:
                    # FRAGMENT_NODE
                    result.append(FragmentNode(**child))
            return result

    @property
    def as_dict(self):
        """
        JSON serializable.
        """
        result = {
            "nodeType": 1,
            "tagName": self.tagName,
            "childNodes": [child.as_dict for child in self.childNodes],
        }
        if self.attributes:
            result["attributes"] = self.attributes
        if self.tagName == "textarea":
            result["value"] = self.value
        return result

    def find(self, selector):
        """
        Recursively check this node, and its children, and return a result
        representing nodes that match "selector" string. The selector
        string understands:

        * #my-id - returns the first ElementNode with the id "my-id". Returns
          None if no match is found.
        * .my-class - returns a list containing elements with the class
          "my-class". Returns an empty list if no match is found.
        * li - returns a list containing elements with the tagName "li".
          Returns an empty list if no match is found.
        """
        # Validate selector.
        if not selector:
            raise ValueError("Missing selector.")
        if selector[0] == "#":
            # Select by unique id.
            target_id = selector[1:]
            if target_id:
                return self._find_by_id(target_id)
            else:
                raise ValueError("Invalid id.")
        elif selector[0] == ".":
            # Select by css class.
            target_class = selector[1:]
            if target_class:
                return self._find_by_class(target_class)
            else:
                raise ValueError("Invalid class.")
        else:
            # select by tagName.
            if selector.isalpha():
                return self._find_by_tagName(selector.lower())
            else:
                raise ValueError("Invalid tag name.")

    def _find_by_id(self, target):
        """
        Return this node, or the first of its children, if it has the id
        attribute of target. Returns None if no match is found.
        """
        my_id = self.attributes.get("id")
        if my_id and my_id == target:
            return self
        else:
            for child in (
                node
                for node in self.childNodes
                if isinstance(node, ElementNode)
            ):
                result = child._find_by_id(target)
                if result:
                    return result
        return None

    def _find_by_class(self, target):
        """
        Return a list containing this node, or any of its children, if the
        node has the associated target class.
        """
        result = []
        class_attr = self.attributes.get("class", "")
        if class_attr:
            classes = [
                class_name
                for class_name in class_attr.split(" ")
                if class_name
            ]
            if target in classes:
                result.append(self)
        for child in (
            node for node in self.childNodes if isinstance(node, ElementNode)
        ):
            result.extend(child._find_by_class(target))
        return result

    def _find_by_tagName(self, target):
        """
        Return a list containing this node, or any of its children, if the
        node has the associated target as its tagName (e.g. "div" or "p").
        """
        result = []
        if self.tagName == target:
            result.append(self)
        for child in (
            node for node in self.childNodes if isinstance(node, ElementNode)
        ):
            result.extend(child._find_by_tagName(target))
        return result


class TextNode(Node):
    """
    Textual content inside an ElementNode.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nodeValue = kwargs.get("nodeValue")

    @property
    def outerHTML(self):
        """
        Get a string representation of the element's outer HTML.
        """
        return self.nodeValue

    @property
    def as_dict(self):
        """
        JSON serializable.
        """
        return {
            "nodeType": 3,
            "nodeName": "#text",
            "nodeValue": self.nodeValue,
            "childNodes": [],
        }


class CommentNode(Node):
    """
    A comment such as <!-- ... -->
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nodeValue = kwargs.get("nodeValue")

    @property
    def outerHTML(self):
        """
        Get a string representation of the element's outer HTML.
        """
        return "<!--" + self.nodeValue + "-->"

    @property
    def as_dict(self):
        """
        JSON serializable.
        """
        return {
            "nodeType": 8,
            "nodeName": "#comment",
            "nodeValue": self.nodeValue,
            "childNodes": [],
        }


class FragmentNode(Node):
    """
    A minimal node when no other type is appropriate.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def outerHTML(self):
        """
        Get a string representation of the element's outer HTML.
        """
        return ""

    @property
    def as_dict(self):
        """
        JSON serializable.
        """
        return {"nodeType": 11, "childNodes": []}


def get_listener_id(query, event_type, listener):
    """
    Given a query, event type and listener function, generate a unique id from
    this combination.
    """
    raw = query.raw_query + event_type + listener.__name__
    return binascii.hexlify(
        hashlib.sha256(raw.encode("utf-8")).digest()
    ).decode("ascii")


def print(*args, **kwargs):
    """
    Overridden print so output is handled correctly via JSON message passing
    instead of just raw text.
    """
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    content = sep.join(args) + end
    builtins.print(json.dumps({"type": "stdout", "content": content}))


def update(query, target):
    """
    Update the DOM so the node[s] matching the query are mutated to the state
    defined by the target node.
    """
    q = Query(query)
    builtins.print(
        json.dumps(
            {
                "type": "updateDOM",
                "query": q.as_dict,
                "target": target.as_dict,
            }
        )
    )


def remove(query, event_type, listener):
    """
    Remove the referenced listener from handling the event_type from the
    node[s] matching the query.
    """
    q = Query(query)
    listener_id = get_listener_id(q, event_type, listener)
    del LISTENERS[listener_id]
    builtins.print(
        json.dumps(
            {
                "type": "removeEvent",
                "query": q.as_dict,
                "eventType": event_type,
            }
        )
    )


def plug(query, event_type):
    """
    Plug a Python function into a DOM event.

    The event is specified by a query to match elements in the DOM tree, and
    an event_type (e.g. "click").

    Returns a decorator function that wraps the user's own function that is
    to be registered.

    This decorator wrapper function creates a closure in which various
    contextual aspects are contained and run.
    """
    q = Query(query)

    def decorator(fn):
        """
        Register the function via the query and event_type.
        """

        def wrapper(event):
            return fn(event)

        listener_id = get_listener_id(q, event_type, wrapper)
        builtins.print(
            json.dumps(
                {
                    "type": "registerEvent",
                    "query": q.as_dict,
                    "eventType": event_type,
                    "listener": listener_id,
                }
            )
        )

        LISTENERS[listener_id] = wrapper
        return wrapper

    return decorator


def receive(raw):
    """
    Given a raw JSON message, decode it, find the expected handler function,
    re-constitute the DOM, and call the handler with the appropriate context.
    """
    try:
        msg = json.loads(raw)
        event_type = msg.get("type")
        target = msg.get("target")
        listener = msg.get("listener")
        if event_type and target and listener:
            if listener in LISTENERS:
                event = DomEvent(event_type, ElementNode(**target))
                LISTENERS[listener](event)
            else:
                raise RuntimeError("No such listener: " + listener)
        else:
            raise ValueError("Incomplete message received: " + raw)
    except Exception as ex:
        context = {"type": type(ex).__name__, "msg": str(ex)}
        builtins.print(
            json.dumps(
                {
                    "type": "error",
                    "context": context,
                }
            )
        )
