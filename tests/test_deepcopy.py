from earn_app._utils import deepcopy_minimal


def assert_different_identities(obj1: object, obj2: object) -> None:
    """
    Assert that two objects are equal in value but have different memory identities.
    
    Raises an AssertionError if the objects are not equal or share the same identity.
    """
    assert obj1 == obj2
    assert id(obj1) != id(obj2)


def test_simple_dict() -> None:
    """
    Test that a simple dictionary is deeply copied by deepcopy_minimal, resulting in equal but distinct objects.
    """
    obj1 = {"foo": "bar"}
    obj2 = deepcopy_minimal(obj1)
    assert_different_identities(obj1, obj2)


def test_nested_dict() -> None:
    """
    Test that a nested dictionary is deeply copied by `deepcopy_minimal`, ensuring both the outer and inner dictionaries have different identities but are equal in value.
    """
    obj1 = {"foo": {"bar": True}}
    obj2 = deepcopy_minimal(obj1)
    assert_different_identities(obj1, obj2)
    assert_different_identities(obj1["foo"], obj2["foo"])


def test_complex_nested_dict() -> None:
    """
    Test that deepcopy_minimal creates deep copies of all nested elements in a complex dictionary structure.
    
    Verifies that the top-level dictionary, nested dictionary, nested list, and innermost dictionary all have different identities in the copy, while remaining equal in value.
    """
    obj1 = {"foo": {"bar": [{"hello": "world"}]}}
    obj2 = deepcopy_minimal(obj1)
    assert_different_identities(obj1, obj2)
    assert_different_identities(obj1["foo"], obj2["foo"])
    assert_different_identities(obj1["foo"]["bar"], obj2["foo"]["bar"])
    assert_different_identities(obj1["foo"]["bar"][0], obj2["foo"]["bar"][0])


def test_simple_list() -> None:
    """
    Test that a simple list is deeply copied by `deepcopy_minimal`, ensuring the copy is equal but has a different identity.
    """
    obj1 = ["a", "b", "c"]
    obj2 = deepcopy_minimal(obj1)
    assert_different_identities(obj1, obj2)


def test_nested_list() -> None:
    """
    Test that deepcopy_minimal creates a deep copy of a nested list, ensuring both the outer and inner lists have different identities but are equal in value.
    """
    obj1 = ["a", [1, 2, 3]]
    obj2 = deepcopy_minimal(obj1)
    assert_different_identities(obj1, obj2)
    assert_different_identities(obj1[1], obj2[1])


class MyObject: ...


def test_ignores_other_types() -> None:
    # custom classes
    """
    Test that `deepcopy_minimal` does not copy custom class instances or tuples, preserving their original identities.
    """
    my_obj = MyObject()
    obj1 = {"foo": my_obj}
    obj2 = deepcopy_minimal(obj1)
    assert_different_identities(obj1, obj2)
    assert obj1["foo"] is my_obj

    # tuples
    obj3 = ("a", "b")
    obj4 = deepcopy_minimal(obj3)
    assert obj3 is obj4
