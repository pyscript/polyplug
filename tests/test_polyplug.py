"""
Exercise PolyPlug.
"""
import copy
import json
import pytest
import polyplug


DOM_FROM_JSON = {
    "nodeType": 1,
    "tagName": "div",
    "attributes": {
        "id": "test-node",
        "style": "font-weight: bold;",
        "custom-attribute": "",
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
                    "childNodes": [],
                }
            ],
        },
        {
            "nodeType": 8,
            "nodeName": "#comment",
            "nodeValue": " A comment ",
            "childNodes": [],
        },
        {
            "nodeType": 1,
            "tagName": "form",
            "childNodes": [
                {
                    "nodeType": 1,
                    "tagName": "label",
                    "attributes": {"for": "testInput"},
                    "childNodes": [
                        {
                            "nodeType": 3,
                            "nodeName": "#text",
                            "nodeValue": "Test Input",
                            "childNodes": [],
                        }
                    ],
                },
                {
                    "nodeType": 1,
                    "tagName": "input",
                    "attributes": {
                        "type": "text",
                        "name": "testInput",
                        "value": "test",
                    },
                    "childNodes": [],
                },
                {
                    "nodeType": 1,
                    "tagName": "textarea",
                    "value": "Some free text content...",
                    "childNodes": [],
                },
                {
                    "nodeType": 1,
                    "tagName": "input",
                    "attributes": {"type": "submit", "value": "Submit"},
                    "childNodes": [],
                },
            ],
        },
        {
            "nodeType": 1,
            "tagName": "ul",
            "attributes": {"id": "list"},
            "childNodes": [
                {"nodeType": 11, "childNodes": []},
                {
                    "nodeType": 1,
                    "tagName": "li",
                    "childNodes": [
                        {
                            "nodeType": 3,
                            "nodeName": "#text",
                            "nodeValue": "a",
                            "childNodes": [],
                        }
                    ],
                },
                {
                    "nodeType": 1,
                    "tagName": "li",
                    "childNodes": [
                        {
                            "nodeType": 3,
                            "nodeName": "#text",
                            "nodeValue": "b",
                            "childNodes": [],
                        }
                    ],
                },
                {
                    "nodeType": 1,
                    "tagName": "li",
                    "childNodes": [
                        {
                            "nodeType": 3,
                            "nodeName": "#text",
                            "nodeValue": "c",
                            "childNodes": [],
                        }
                    ],
                },
            ],
        },
    ],
}


def test_query_id():
    """
    A query object based on HTML id.
    """
    q = polyplug.Query(id="myId")
    assert q.id == "myId"


def test_query_tag():
    """
    A query object based on HTML tag.
    """
    q = polyplug.Query(tag="p")
    assert q.tag == "p"


def test_query_classname():
    """
    A query object based on CSS class.
    """
    q = polyplug.Query(classname="my-css-class")
    assert q.classname == "my-css-class"


def test_query_css():
    """
    A query object based on CSS selector.
    """
    q = polyplug.Query(css="p.myClass")
    assert q.css == "p.myClass"


def test_query_as_dict():
    """
    A JSON serializable dict object is returned.
    """
    q = polyplug.Query(id="myId")
    expected = json.dumps(q.as_dict)
    assert expected == '{"id": "myId"}'


def test_query_invalid_missing_type():
    """
    An invalid instantiation of Query results in a ValueError.

    Missing one of the expected query specification types.
    """
    with pytest.raises(ValueError):
        polyplug.Query(foo="bar")


def test_query_invalid_too_many_types():
    """
    An invalid instantiation of Query results in a ValueError.

    There should only be one type of query specification.
    """
    with pytest.raises(ValueError):
        polyplug.Query(id="myId", tag="p")


def test_dom_event():
    """
    The event is instantiated in the expected manner.
    """
    target = polyplug.Node()
    e = polyplug.DomEvent("click", target)
    assert e.event_type == "click"
    assert e.target == target


def test_node():
    """
    The Node class is instantiated in the expected manner.
    """
    n = polyplug.Node(a=1, b=2)
    assert n._node["a"] == 1
    assert n._node["b"] == 2
    assert n.parent is None
    assert n.as_dict is NotImplemented


def test_node_with_parent():
    """
    The Node will keep a reference to the parent if needed.
    """
    n = polyplug.Node(parent="fakeParent")
    assert n.parent == "fakeParent"


def test_attributes():
    """
    The Attributes instantiates correctly from the dict.
    """
    a = polyplug.Attributes({"foo": "bar"})
    assert a.foo == "bar"


def test_attributes_get_set_del():
    """
    Get/set/del interactions with the Arributes work as expected.
    """
    a = polyplug.Attributes({})
    with pytest.raises(AttributeError):
        a.foo
    a.foo = "bar"
    assert a.foo == "bar"
    del a.foo
    with pytest.raises(AttributeError):
        del a.foo


def test_attributes_to_json():
    """
    An Attribute instance is JSON encodeable.
    """
    a = polyplug.Attributes({"foo": "bar"})
    assert json.dumps(a) == '{"foo": "bar"}'


def test_element_node_init_basic():
    """
    The ElementNode instantiates in the expected manner.
    """
    n = polyplug.ElementNode(tagName="div", parent="fakeParent")
    assert n.tagName == "div"
    assert n.attributes == {}
    assert n.childNodes == []
    assert n.parent == "fakeParent"


def test_element_node_init_attributes():
    """
    The ElementNode instantiates in the expected manner with attributes.
    """
    n = polyplug.ElementNode(tagName="div", attributes={"foo": "bar"})
    assert n.tagName == "div"
    assert n.attributes.foo == "bar"
    assert n.childNodes == []


def test_element_node_as_textarea():
    """
    The textarea node type is special in that it doesn't have children. There
    is only a (text) value. E.g.:

    <textarea>text value</textarea>
    """
    n = polyplug.ElementNode(
        tagName="textarea", attributes={"class": "myClass"}, value="text value"
    )
    assert n.tagName == "textarea"
    assert n.value == "text value"
    assert n.childNodes == []
    assert n.attributes["class"] == "myClass"


def test_element_node_init_complex_children():
    """
    The ElementNode instantiates in the expected manner with complex children
    nodes.

    The complex structure is re-constituted back to the expected dict object
    which can be JSON serialised.
    """
    raw_dom = copy.deepcopy(DOM_FROM_JSON)
    n = polyplug.ElementNode(**raw_dom)
    to_jsonify = n.as_dict
    assert to_jsonify == DOM_FROM_JSON
    assert json.dumps(to_jsonify)


def test_element_node_add_child_as_node():
    """
    It's possible to add a child node that is a Node type.
    """
    n = polyplug.ElementNode(tagName="div", attributes={"foo": "bar"})
    assert n.childNodes == []
    child = polyplug.TextNode(nodeValue="Hello")
    n.add_child(child)
    assert len(n.childNodes) == 1
    new_child = n.childNodes[0]
    assert isinstance(new_child, polyplug.TextNode) is True
    assert new_child.nodeValue == "Hello"


def test_element_node_add_child_as_dict():
    """
    It's possible to add a child node that is represented as a dict.
    """
    n = polyplug.ElementNode(tagName="div", attributes={"foo": "bar"})
    assert n.childNodes == []
    child = polyplug.TextNode(nodeValue="Hello").as_dict
    n.add_child(child)
    assert len(n.childNodes) == 1
    new_child = n.childNodes[0]
    assert isinstance(new_child, polyplug.TextNode) is True
    assert new_child.nodeValue == "Hello"


def test_text_node():
    """
    The TextNode instantiates as expected.
    """
    n = polyplug.TextNode(
        nodeType=3,
        nodeName="#text",
        nodeValue="Test text.",
        parent="fakeParent",
    )
    assert n.nodeValue == "Test text."
    assert n.parent == "fakeParent"


def test_comment_node():
    """
    The CommentNode instantiates as expected.
    """
    n = polyplug.CommentNode(
        nodeType=8,
        nodeName="#comment",
        nodeValue="Test comment.",
        parent="fakeParent",
    )
    assert n.nodeValue == "Test comment."
    assert n.parent == "fakeParent"


def test_fragment_node():
    """
    The FragmentNode instantiates as expected.
    """
    n = polyplug.FragmentNode(
        nodeType=11,
        nodeName="#fragment",
        parent="fakeParent",
    )
    assert n.parent == "fakeParent"


def test_htmltokenizer_init():
    """
    The HTMLTokenizer class instantiates to the expected state.
    """
    tok = polyplug.HTMLTokenizer("<p>Hello</p>")
    assert tok.raw == "<p>Hello</p>"
    assert tok.len == len(tok.raw)
    assert tok.char == "<"
    assert tok.pos == 1
    tok = polyplug.HTMLTokenizer("")
    assert tok.raw == ""
    assert tok.len == 0
    assert tok.pos == 0
    assert tok.char == ""


def test_htmltokenizer_next_char():
    """
    The next_char method keeds setting and returning the next character in the
    HTML string, until it reaches the end, then just returns empty string.
    """
    raw = "<p>Hello</p>"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.char == "<"
    for i, character in enumerate(raw[1:], start=1):
        assert i == tok.pos
        result = tok.next_char()
        assert result == character
    assert tok.next_char() == ""


def test_htmltokenizer_get_char():
    """
    Ensure get_char gets the current character and moves the position forward
    by one step.
    """
    raw = "<p>Hello</p>"
    tok = polyplug.HTMLTokenizer(raw)
    for i, character in enumerate(raw, start=1):
        assert i == tok.pos
        result = tok.get_char()
        assert result == character
    assert tok.next_char() == ""


def test_htmltokenizer_skip_ws():
    """
    Ensure whitespace skipping works as expected. Just ignore the whitespace
    until the next non-space character if encountered.
    """
    # Content with whitespace.
    raw = "\n\t     <p>Hello</p>"
    tok = polyplug.HTMLTokenizer(raw)
    tok.skip_ws()
    assert tok.char == "<"
    assert tok.pos == 8
    # No content.
    tok = polyplug.HTMLTokenizer("")
    tok.skip_ws()
    assert tok.char == ""
    assert tok.pos == 0


def test_htmltokenizer_match():
    """
    Ensure the next non-whitespace character matches the expected outcome.
    """
    raw = "\n\t     <p>Hello</p>"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.match("<") is True
    assert tok.match("!") is False


def test_htmltokenizer_match_multiple_expected():
    """
    Ensure the next non-whitespace character matches one of the several
    expected outcomes.
    """
    raw = "\n\t     <p>Hello</p>"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.match("><") is True
    assert tok.match("!") is False


def test_htmltokenizer_expect():
    """
    Do nothing if the next non-whitespace character is the expected outcome,
    otherwise raise a ValueError exception.
    """
    raw = "\n\t     <p>Hello</p>"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.expect("<") is None
    with pytest.raises(ValueError):
        tok.expect("!")


def test_htmltokenizer_get_name():
    """
    Given a potential tagName or attribute name, grab and return it.
    """
    # tagName (assume a "<" character was followed by the raw string)
    raw = "\n\t  div id='foo'"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_name() == "div"
    assert tok.char == " "
    # attribute name (assume a "<div" was followed by the raw string)
    raw = "\n\t  id='foo'"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_name() == "id"
    assert tok.expect("=") is None


def test_htmltokenizer_get_value():
    """
    Given a potential value for an attribute, grab and return it.
    """
    raw = "='foo'>"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_value() == "foo"
    assert tok.expect(">") is None


def test_htmltokenizer_get_attrs_has_attrs():
    """
    If the next part of the string represents valid attributes, ensure the
    expected Attributes instance is returned.
    """
    raw = " id='foo' no_value class=\"myCssClass\">"
    tok = polyplug.HTMLTokenizer(raw)
    attrs = tok.get_attrs()
    assert attrs.id == "foo"
    assert attrs.no_value == ""
    assert attrs["class"] == "myCssClass"
    assert len(attrs) == 3


def test_htmltokenizer_get_attrs_no_attributes():
    """
    If there are no attributes to parse, just return an empty Attributes
    object.
    """
    raw = ">"
    tok = polyplug.HTMLTokenizer(raw)
    attrs = tok.get_attrs()
    assert len(attrs) == 0


def test_htmltokenizer_get_text():
    """
    Get the textual content of a TextNode (i.e. everything until encountering
    "<").
    """
    raw = "Hello, world!<"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_text() == "Hello, world!"
    assert tok.char == "<"


def test_htmltokenizer_get_text_until():
    """
    Get the textual content of a TextNode (i.e. everything until encountering
    the passed in "until" fragment).
    """
    raw = "Hello, world!</textarea>"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_text(until="</textarea>") == "Hello, world!"
    assert tok.char == "<"


def test_htmltokenizer_get_text_empty_with_until():
    """
    No more text = empty string.
    """
    raw = ""
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_text(until="</textarea>") == ""
    assert tok.char == ""


def test_htmltokenizer_get_text_empty():
    """
    No more text = empty string.
    """
    raw = ""
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_text() == ""
    assert tok.char == ""


def test_htmltokenizer_tokenize():
    """
    Must have a valid parent.
    """
    raw = ""
    tok = polyplug.HTMLTokenizer(raw)
    with pytest.raises(ValueError):
        tok.tokenize(parent="foo")


def test_htmltokenizer_tokenize_comment():
    """
    Given a valid parent, a comment is added as a child from the raw input.
    """
    parent = polyplug.ElementNode(tagName="div")
    raw = "<!-- Test comment. -->"
    tok = polyplug.HTMLTokenizer(raw)
    tok.tokenize(parent)
    assert len(parent.childNodes) == 1
