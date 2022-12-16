"""
Exercise PolyPlug.
"""
import copy
import json
import pytest
import polyplug
from unittest import mock


@pytest.fixture(autouse=True)
def test_wrapper():
    """
    Ensures clean state.
    """
    # Clear the listeners.
    polyplug.LISTENERS = {}
    # Run the test.
    yield
    # ???
    # Profit!


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
                    },
                    "value": "test",
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
    q = polyplug.Query("#myId")
    assert q.id == "myId"
    assert q.raw_query == "#myId"
    with pytest.raises(ValueError):
        polyplug.Query("#")


def test_query_tag():
    """
    A query object based on HTML tag.
    """
    q = polyplug.Query("p")
    assert q.tag == "p"
    assert q.raw_query == "p"


def test_query_classname():
    """
    A query object based on CSS class.
    """
    q = polyplug.Query(".my-css-class")
    assert q.classname == "my-css-class"
    assert q.raw_query == ".my-css-class"
    with pytest.raises(ValueError):
        polyplug.Query(".")


def test_query_css():
    """
    A query object based on CSS selector.
    """
    q = polyplug.Query("p.myClass")
    assert q.css == "p.myClass"
    assert q.raw_query == "p.myClass"


def test_query_as_dict():
    """
    A JSON serializable dict object is returned.
    """
    q = polyplug.Query("#myId")
    expected = json.dumps(q.as_dict)
    assert expected == '{"id": "myId"}'


def test_query_invalid_missing_selector():
    """
    An invalid instantiation of Query results in a ValueError.
    """
    with pytest.raises(ValueError):
        polyplug.Query("")


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
    assert n.outerHTML is NotImplemented
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


def test_element_node_get_outer_html():
    """
    Get a string representation of the node's complete structure.
    """
    n = polyplug.ElementNode(tagName="div", attributes={"foo": "bar"})
    n.add_child(polyplug.TextNode(nodeValue="Hello"))
    assert n.outerHTML == '<div foo="bar">Hello</div>'


def test_element_node_get_inner_html_empty():
    """
    Get a string representation of the node's inner structure. Empty.
    """
    n = polyplug.ElementNode(tagName="div", attributes={"foo": "bar"})
    assert n.innerHTML == ""


def test_element_node_get_set_inner_html_complex():
    """
    Get a string representation of the node's inner structure.
    """
    n = polyplug.ElementNode(tagName="div", attributes={"foo": "bar"})
    n.innerHTML = "<!-- comment --><p>Hello</p>"
    assert n.innerHTML == "<!-- comment --><p>Hello</p>"


def test_element_node_set_inner_html_empty():
    """
    Set the innerHTML of the node as empty.
    """
    n = polyplug.ElementNode(tagName="div", attributes={"foo": "bar"})
    n.innerHTML = "<!-- comment --><p>Hello</p>"
    n.innerHTML = ""
    assert n.innerHTML == ""


def test_element_node_set_inner_html_textarea():
    """
    Set the innerHTML of the node as a textarea.
    """
    n = polyplug.ElementNode(tagName="div", attributes={"foo": "bar"})
    n.innerHTML = "<textarea>Test <fake html></textarea>"
    assert n.innerHTML == "<textarea>Test <fake html></textarea>"


def test_element_node_find():
    """
    The find method validates the selector.
    """
    # Can't be empty.
    selector = ""
    n = polyplug.ElementNode(tagName="div")
    with pytest.raises(ValueError):
        n.find(selector)
    # Must be a valid id.
    selector = "#my-id"  # valid
    n._find_by_id = mock.MagicMock()
    n.find(selector)
    n._find_by_id.assert_called_once_with("my-id")
    selector = "#"  # in-valid
    with pytest.raises(ValueError):
        n.find(selector)
    # Must be a valid class.
    selector = ".my-class"  # valid
    n._find_by_class = mock.MagicMock()
    n.find(selector)
    n._find_by_class.assert_called_once_with("my-class")
    selector = "."  # in-valid
    with pytest.raises(ValueError):
        n.find(selector)
    # Must be a valid tagName.
    selector = "tagName"  # valid
    n._find_by_tagName = mock.MagicMock()
    n.find(selector)
    n._find_by_tagName.assert_called_once_with("tagname")  # lowercase!
    selector = "not a tag name because spaces etc"  # in-valid
    with pytest.raises(ValueError):
        n.find(selector)


def test_element_node_find_by_id():
    """
    The expected individual nodes are returned for various combinations of
    searching the tree by unique id.
    """
    # Will return itself as the first match.
    n = polyplug.ElementNode(tagName="div", attributes={"id": "foo"})
    assert n == n.find("#foo")
    # Will return the expected child.
    n = polyplug.ElementNode(tagName="div")
    n.innerHTML = "<ul><li>Nope</li><li id='foo'>Yup</li></ul>"
    result = n.find("#foo")
    assert isinstance(result, polyplug.ElementNode)
    assert result.innerHTML == "Yup"
    # Returns None if no match.
    assert n.find("#bar") is None


def test_element_node_find_by_class():
    """
    The expected collection of matching nodes are returned for various
    combinations of searching the tree by CSS class.
    """
    # Returns itself if matched.
    n = polyplug.ElementNode(tagName="div", attributes={"class": "foo"})
    assert [
        n,
    ] == n.find(".foo")
    # Returns expected children (along with itself).
    n = polyplug.ElementNode(tagName="div", attributes={"class": "foo"})
    n.innerHTML = "<ul><li class='foo'>Yup</li><li class='foo'>Yup</li></ul>"
    result = n.find(".foo")
    assert len(result) == 3
    assert result[0] == n
    assert result[1].tagName == "li"
    assert result[2].tagName == "li"
    # Returns just expected children (not itself).
    n = polyplug.ElementNode(tagName="div", attributes={"class": "bar"})
    n.innerHTML = "<ul><li class='foo'>Yup</li><li class='foo'>Yup</li></ul>"
    result = n.find(".foo")
    assert len(result) == 2
    assert result[0].tagName == "li"
    assert result[1].tagName == "li"
    # Returns just expected children with multiple classes.
    n = polyplug.ElementNode(tagName="div", attributes={"class": "bar foo"})
    n.innerHTML = (
        "<ul><li class='foo bar'>Yup</li><li class='foobar'>Nope</li></ul>"
    )
    result = n.find(".foo")
    assert len(result) == 2
    assert result[0] == n
    assert result[1].tagName == "li"
    # No match returns an empty list.
    n = polyplug.ElementNode(tagName="div", attributes={"class": "bar"})
    n.innerHTML = "<ul><li class='foo'>Nope</li><li class='foo'>Nope</li></ul>"
    result = n.find(".baz")
    assert result == []


def test_element_node_find_by_tagName():
    """
    The expected collection of matching nodes are returned for various
    combinations of searching the tree by tagName.
    """
    # Returns itself if matched.
    n = polyplug.ElementNode(tagName="div")
    assert [
        n,
    ] == n.find("div")
    # Returns expected children (along with itself).
    n = polyplug.ElementNode(tagName="li")
    n.innerHTML = "<ul><li>Yup</li><li>Yup</li></ul>"
    result = n.find("li")
    assert len(result) == 3
    assert result[0] == n
    assert result[1].innerHTML == "Yup"
    assert result[2].innerHTML == "Yup"
    # Returns just expected children (not itself).
    n = polyplug.ElementNode(tagName="div")
    n.innerHTML = "<ul><li>Yup</li><li>Yup</li></ul>"
    result = n.find("li")
    assert len(result) == 2
    assert result[0].innerHTML == "Yup"
    assert result[1].innerHTML == "Yup"
    # No match returns an empty list.
    n = polyplug.ElementNode(tagName="div")
    n.innerHTML = "<ul><li>Nope</li><li>Nope</li></ul>"
    result = n.find("p")
    assert result == []


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
    assert n.outerHTML == "Test text."


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
    assert n.outerHTML == "<!--Test comment.-->"


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
    assert n.outerHTML == ""


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
    raw = "='font: arial; font-weight: bold!important;'>"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_value() == "font: arial; font-weight: bold!important;"
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
    raw = "Hello, world!<div>"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_text() == "Hello, world!"
    assert tok.char == "<"


def test_htmltokenizer_get_text_bound_check():
    """
    Get the textual content of a TextNode (i.e. everything until encountering
    "<").
    """
    raw = "Hello, world!<"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_text() == "Hello, world!"
    assert tok.char == "<"


def test_htmltokenizer_get_text_eof():
    """
    Get the textual content of a TextNode (i.e. everything until encountering
    "<").
    """
    raw = "Hello, world!"
    tok = polyplug.HTMLTokenizer(raw)
    assert tok.get_text() == "Hello, world!"
    assert tok.char == ""


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
    assert isinstance(parent.childNodes[0], polyplug.CommentNode)
    assert parent.childNodes[0].nodeValue == " Test comment. "


def test_htmltokenizer_tokenize_prolog():
    """
    Given a valid parent, an XML prolog node is ignored. <? foo ?>
    """
    parent = polyplug.ElementNode(tagName="div")
    raw = "<? xml ?>"
    tok = polyplug.HTMLTokenizer(raw)
    tok.tokenize(parent)
    assert len(parent.childNodes) == 0


def test_htmltokenizer_tokenize_text():
    """
    Textual content becomes a child TextNode.
    """
    parent = polyplug.ElementNode(tagName="div")
    raw = "Test text."
    tok = polyplug.HTMLTokenizer(raw)
    tok.tokenize(parent)
    assert len(parent.childNodes) == 1
    assert isinstance(parent.childNodes[0], polyplug.TextNode)
    assert parent.childNodes[0].nodeValue == "Test text."


def test_htmltokenizer_tokenize_element():
    """
    An HTML element becomes a child ElementNode.
    """
    parent = polyplug.ElementNode(tagName="div")
    raw = "<p>Hello</p>"
    tok = polyplug.HTMLTokenizer(raw)
    tok.tokenize(parent)
    assert len(parent.childNodes) == 1
    p_node = parent.childNodes[0]
    assert isinstance(p_node, polyplug.ElementNode)
    assert len(p_node.childNodes) == 1
    assert isinstance(p_node.childNodes[0], polyplug.TextNode)
    assert p_node.childNodes[0].nodeValue == "Hello"


def test_htmltokenizer_tokenize_element_textarea():
    """
    An HTML element becomes a child ElementNode. But textarea nodes will only
    have a value (no children) containing the text within the tags.
    """
    parent = polyplug.ElementNode(tagName="div")
    raw = "<textarea>Hello <fake-html></textarea>"
    tok = polyplug.HTMLTokenizer(raw)
    tok.tokenize(parent)
    assert len(parent.childNodes) == 1
    textarea = parent.childNodes[0]
    assert isinstance(textarea, polyplug.ElementNode)
    assert len(textarea.childNodes) == 0
    assert textarea.value == "Hello <fake-html>"


def test_htmltokenizer_tokenize_element_unexpected():
    """
    An unexpected close tag results in a ValueError.
    """
    parent = polyplug.ElementNode(tagName="div")
    raw = "</textarea>"
    tok = polyplug.HTMLTokenizer(raw)
    with pytest.raises(ValueError):
        tok.tokenize(parent)


def test_htmltokenizer_tokenize_complex_tree():
    """
    A more complex tree with several branches and node types.
    """
    parent = polyplug.ElementNode(tagName="div")
    raw = "<!-- comment --><div id='myId'><p>Hello</p><p>world</p></div>"
    expected = {
        "childNodes": [
            {
                "childNodes": [],
                "nodeName": "#comment",
                "nodeType": 8,
                "nodeValue": " comment ",
            },
            {
                "attributes": {"id": "myId"},
                "childNodes": [
                    {
                        "childNodes": [
                            {
                                "childNodes": [],
                                "nodeName": "#text",
                                "nodeType": 3,
                                "nodeValue": "Hello",
                            }
                        ],
                        "nodeType": 1,
                        "tagName": "p",
                    },
                    {
                        "childNodes": [
                            {
                                "childNodes": [],
                                "nodeName": "#text",
                                "nodeType": 3,
                                "nodeValue": "world",
                            }
                        ],
                        "nodeType": 1,
                        "tagName": "p",
                    },
                ],
                "nodeType": 1,
                "tagName": "div",
            },
        ],
        "nodeType": 1,
        "tagName": "div",
    }
    tok = polyplug.HTMLTokenizer(raw)
    tok.tokenize(parent)
    assert parent.as_dict == expected


def test_get_listener_id():
    """
    Return a string containing a hex representation of a sha256 hash of the
    passed in Query, event type and listener function.
    """
    query = polyplug.Query("#foo")
    event_type = "click"

    def test_fn():
        pass

    id_1 = polyplug.get_listener_id(query, event_type, test_fn)
    id_2 = polyplug.get_listener_id(query, event_type, test_fn)
    assert id_1 == id_2  # These should be the same..!


def test_print():
    """
    The polyplug print function emits the expected JSON message.
    """
    with mock.patch("builtins.print") as mock_print:
        # Simple case with defaults.
        polyplug.print("Hello", "world")
        mock_print.assert_called_once_with(
            '{"type": "stdout", "content": "Hello world\\n"}'
        )
        mock_print.reset_mock()
        # More complex with sep and end
        polyplug.print("Hello", "world", sep="-", end="")
        mock_print.assert_called_once_with(
            '{"type": "stdout", "content": "Hello-world"}'
        )


def test_update():
    """
    Given a query object and a representation of a target node, the expected
    updateDOM message is emitted, with the correct payload.
    """
    query = "#foo"
    raw_dom = copy.deepcopy(DOM_FROM_JSON)
    target = polyplug.ElementNode(**raw_dom)
    with mock.patch("builtins.print") as mock_print:
        polyplug.update(query, target)
        assert mock_print.call_count == 1
        msg = json.loads(mock_print.call_args.args[0])
        assert msg["type"] == "updateDOM"
        assert msg["query"]["id"] == "foo"
        assert msg["target"] == DOM_FROM_JSON


def test_remove():
    """
    The expected message is emitted when the referenced listener is marked to
    be removed from handling the event type, for the nodes in the DOM matched
    by the Query object.
    """
    with mock.patch("builtins.print") as mock_print:

        @polyplug.plug("#foo", "some-event")
        def test_fn(event):
            return "It works!"

        assert mock_print.call_count == 1
        listener_id = polyplug.get_listener_id(
            polyplug.Query("#foo"), "some-event", test_fn
        )
        assert listener_id in polyplug.LISTENERS
        mock_print.reset_mock()
        polyplug.remove("#foo", "some-event", test_fn)
        assert mock_print.call_count == 1
        msg = json.loads(mock_print.call_args.args[0])
        assert msg["type"] == "removeEvent"
        assert msg["query"]["id"] == "foo"
        assert msg["eventType"] == "some-event"
        assert listener_id not in polyplug.LISTENERS


def test_plug_decorator_register():
    """
    Ensure the expected register JSON message is emitted when the decorator is
    used on a user's function.
    """
    with mock.patch("builtins.print") as mock_print:

        @polyplug.plug("#foo", "some-event")
        def test_fn(event):
            return "It works!"

        assert mock_print.call_count == 1
        msg = json.loads(mock_print.call_args.args[0])
        assert msg["type"] == "registerEvent"
        assert msg["listener"] == polyplug.get_listener_id(
            polyplug.Query("#foo"), "some-event", test_fn
        )
        assert msg["query"]["id"] == "foo"
        assert msg["eventType"] == "some-event"
        result = polyplug.LISTENERS[msg["listener"]](None)
        assert result == "It works!"


def test_receive_bad_json():
    """
    If the receive function get a non-JSON message, it complains with an error
    message of its own.
    """
    with mock.patch("builtins.print") as mock_print:
        polyplug.receive("not VALID")
        assert mock_print.call_count == 1
        msg = json.loads(mock_print.call_args.args[0])
        assert msg["type"] == "error"
        assert msg["context"]["type"] == "JSONDecodeError"
        assert (
            msg["context"]["msg"]
            == "Expecting value: line 1 column 1 (char 0)"
        )


def test_receive_incomplete_message():
    """
    If the receive function gets valid JSON that is the wrong "shape", it
    complains with a message of its own.
    """
    with mock.patch("builtins.print") as mock_print:
        polyplug.receive(json.dumps({"foo": "bar"}))
        assert mock_print.call_count == 1
        msg = json.loads(mock_print.call_args.args[0])
        assert msg["type"] == "error"
        assert msg["context"]["type"] == "ValueError"
        assert (
            msg["context"]["msg"]
            == 'Incomplete message received: {"foo": "bar"}'
        )


def test_receive_no_listener():
    """
    If the receive function gets a valid message but the referenced listener
    function doesn't exist, it complains with a message of its own.
    """
    with mock.patch("builtins.print") as mock_print:
        polyplug.receive(
            json.dumps(
                {
                    "type": "some-event",
                    "target": DOM_FROM_JSON,
                    "listener": "does_not_exist",
                }
            )
        )
        assert mock_print.call_count == 1
        msg = json.loads(mock_print.call_args.args[0])
        assert msg["type"] == "error"
        assert msg["context"]["type"] == "RuntimeError"
        assert msg["context"]["msg"] == "No such listener: does_not_exist"


def test_receive_for_registered_listener():
    """
    If the receive function gets a valid message for an existing event,
    the function is called with the expected DomEvent object.
    """
    with mock.patch("builtins.print") as mock_print:
        # To be called when there's user defined work to be done.
        mock_work = mock.MagicMock()

        @polyplug.plug("#foo", "some-event")
        def test_fn(event):
            """
            Do some work as if an end user.
            """
            # Expected eventType.
            if event.event_type != "some-event":
                raise ValueError("It broke! Wrong event.")
            # The target represents the expected element.
            if event.target.tagName != "div":
                raise ValueError("It broke! Wrong target root.")
            # It's possible to find one of the expected child nodes.
            ul = event.target.find("#list")
            if ul.tagName != "ul":
                raise ValueError("It broke! Wrong child nodes.")
            # Signal things worked out. ;-)
            mock_work("It works!")

        assert mock_print.call_count == 1
        mock_print.reset_mock()

        listener_id = polyplug.get_listener_id(
            polyplug.Query("#foo"), "some-event", test_fn
        )

        polyplug.receive(
            json.dumps(
                {
                    "type": "some-event",
                    "target": DOM_FROM_JSON,
                    "listener": listener_id,
                }
            )
        )

        mock_work.assert_called_once_with("It works!")
