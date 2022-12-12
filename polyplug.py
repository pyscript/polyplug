import json


def output(content):
    print(json.dumps({"type": "stdout", "content": content}))


class Query:
    """
    A query must have one, and only one, of:

    * id - a unique element id (e.g. "myElementId").
    * tag - a tag name (e.g. "p").
    * classname - a class (e.g. "my-css-class").
    * css - a css selector (e.g "p.className").

    These types of query relate to the four ways in which elements in an HTML
    document may be identified.

    E.g.

    q = Query(id="myElementID")
    """

    # Query type definitions
    ID = "id"
    TAG = "tag"
    CLASSNAME = "classname"
    CSS = "css"
    QUERY_TYPES = (ID, TAG, CLASSNAME, CSS)

    def __init__(self, **kwargs):
        """
        Raise a ValueError if it's not the case that one, and only one of the
        expected types of query is given.
        """
        query_type = [key for key in kwargs if key in self.QUERY_TYPES]
        if len(query_type) == 1:
            self.query_type = query_type[0]
            setattr(self, self.query_type, kwargs[self.query_type])
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
                if not (c.isalpha() or c.isdigit() or c in "_-."):
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
        return NotImplemented

    @property
    def as_dict(self):
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
            result += " " + attr + "=\"" + val + "\""
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
        return {"nodeType": 11, "childNodes": []}


def plug(query, event_type):
    """
    A decorator to plug a Python function into a DOM event specified by a
    query to match elements in the DOM tree, and an event_type (e.g. "click").

    The decorator must ... TODO: FINISH THIS
    """
    pass
