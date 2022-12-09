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
                {
                    "nodeType": 11,
                    "childNodes": []
                },
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
