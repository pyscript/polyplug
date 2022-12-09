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
            raise ValueError(
                "Bad query specification."
            )

    @property
    def as_dict(self):
        """
        Return a dict to be JSON encoded.
        """
        return {self.query_type: getattr(self, self.query_type), }


class DomEvent:
    """
    Represents an event dispatched in the DOM.

    The event_type (e.g. "click") and target (DOM element that was the source
    of the event) are referenced.
    """

    def __init__(self, event_type, target):
        self.event_type = event_type
        self.target = target


class Node:
    """
    Represents a node in the DOM.
    """

    def __init__(self, **kwargs):
        self._node = kwargs
        self.parent = kwargs.get("parent")

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
            "childNodes": [child.as_dict for child in self.childNodes]
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
    def as_dict(self):
        return {
            "nodeType": 3,
            "nodeName": "#text",
            "nodeValue": self.nodeValue,
            "childNodes": []
        }


class CommentNode(Node):
    """
    A comment such as <!-- ... -->
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nodeValue = kwargs.get("nodeValue")

    @property
    def as_dict(self):
        return {
            "nodeType": 8,
            "nodeName": "#comment",
            "nodeValue": self.nodeValue,
            "childNodes": []
        }


class FragmentNode(Node):
    """
    A minimal node when no other type is appropriate.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def as_dict(self):
        return {
            "nodeType": 11,
            "childNodes": []
        }


def plug(query, event_type):
    """
    A decorator to plug a Python function into a DOM event specified by a
    query to match elements in the DOM tree, and an event_type (e.g. "click").

    The decorator must ... TODO: FINISH THIS
    """
    pass
