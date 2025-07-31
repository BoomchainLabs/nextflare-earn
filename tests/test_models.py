import json
from typing import Any, Dict, List, Union, Optional, cast
from datetime import datetime, timezone
from typing_extensions import Literal, Annotated, TypeAliasType

import pytest
import pydantic
from pydantic import Field

from earn_app._utils import PropertyInfo
from earn_app._compat import PYDANTIC_V2, parse_obj, model_dump, model_json
from earn_app._models import BaseModel, construct_type


class BasicModel(BaseModel):
    foo: str


@pytest.mark.parametrize("value", ["hello", 1], ids=["correct type", "mismatched"])
def test_basic(value: object) -> None:
    """
    Tests that a BasicModel instance constructed with a given value assigns the value to the 'foo' field without type coercion or validation.
    """
    m = BasicModel.construct(foo=value)
    assert m.foo == value


def test_directly_nested_model() -> None:
    """
    Tests construction of a model with a directly nested submodel field, verifying correct assignment with both valid and mismatched types.
    """
    class NestedModel(BaseModel):
        nested: BasicModel

    m = NestedModel.construct(nested={"foo": "Foo!"})
    assert m.nested.foo == "Foo!"

    # mismatched types
    m = NestedModel.construct(nested="hello!")
    assert cast(Any, m.nested) == "hello!"


def test_optional_nested_model() -> None:
    """
    Test construction of a model with an optional nested model field using various input types.
    
    Verifies that the nested field can be set to None, a dictionary (which is coerced to the nested model), or a mismatched type (which is preserved as-is without validation).
    """
    class NestedModel(BaseModel):
        nested: Optional[BasicModel]

    m1 = NestedModel.construct(nested=None)
    assert m1.nested is None

    m2 = NestedModel.construct(nested={"foo": "bar"})
    assert m2.nested is not None
    assert m2.nested.foo == "bar"

    # mismatched types
    m3 = NestedModel.construct(nested={"foo"})
    assert isinstance(cast(Any, m3.nested), set)
    assert cast(Any, m3.nested) == {"foo"}


def test_list_nested_model() -> None:
    """
    Test construction of a model with a list of nested models, verifying correct handling of valid and mismatched input types.
    """
    class NestedModel(BaseModel):
        nested: List[BasicModel]

    m = NestedModel.construct(nested=[{"foo": "bar"}, {"foo": "2"}])
    assert m.nested is not None
    assert isinstance(m.nested, list)
    assert len(m.nested) == 2
    assert m.nested[0].foo == "bar"
    assert m.nested[1].foo == "2"

    # mismatched types
    m = NestedModel.construct(nested=True)
    assert cast(Any, m.nested) is True

    m = NestedModel.construct(nested=[False])
    assert cast(Any, m.nested) == [False]


def test_optional_list_nested_model() -> None:
    """
    Test construction of a model with an optional list of nested models, verifying correct handling of valid lists, None, and mismatched types.
    """
    class NestedModel(BaseModel):
        nested: Optional[List[BasicModel]]

    m1 = NestedModel.construct(nested=[{"foo": "bar"}, {"foo": "2"}])
    assert m1.nested is not None
    assert isinstance(m1.nested, list)
    assert len(m1.nested) == 2
    assert m1.nested[0].foo == "bar"
    assert m1.nested[1].foo == "2"

    m2 = NestedModel.construct(nested=None)
    assert m2.nested is None

    # mismatched types
    m3 = NestedModel.construct(nested={1})
    assert cast(Any, m3.nested) == {1}

    m4 = NestedModel.construct(nested=[False])
    assert cast(Any, m4.nested) == [False]


def test_list_optional_items_nested_model() -> None:
    """
    Test construction of a model with a list of optional nested models, including handling of None, dictionaries, and mismatched types.
    """
    class NestedModel(BaseModel):
        nested: List[Optional[BasicModel]]

    m = NestedModel.construct(nested=[None, {"foo": "bar"}])
    assert m.nested is not None
    assert isinstance(m.nested, list)
    assert len(m.nested) == 2
    assert m.nested[0] is None
    assert m.nested[1] is not None
    assert m.nested[1].foo == "bar"

    # mismatched types
    m3 = NestedModel.construct(nested="foo")
    assert cast(Any, m3.nested) == "foo"

    m4 = NestedModel.construct(nested=[False])
    assert cast(Any, m4.nested) == [False]


def test_list_mismatched_type() -> None:
    """
    Test that constructing a model with a list field using a mismatched non-list type preserves the original value without coercion.
    """
    class NestedModel(BaseModel):
        nested: List[str]

    m = NestedModel.construct(nested=False)
    assert cast(Any, m.nested) is False


def test_raw_dictionary() -> None:
    """
    Test construction of a model with a dictionary field, verifying correct assignment and handling of mismatched types.
    """
    class NestedModel(BaseModel):
        nested: Dict[str, str]

    m = NestedModel.construct(nested={"hello": "world"})
    assert m.nested == {"hello": "world"}

    # mismatched types
    m = NestedModel.construct(nested=False)
    assert cast(Any, m.nested) is False


def test_nested_dictionary_model() -> None:
    """
    Test construction of a model with a dictionary of nested models, verifying correct instantiation and handling of mismatched types.
    """
    class NestedModel(BaseModel):
        nested: Dict[str, BasicModel]

    m = NestedModel.construct(nested={"hello": {"foo": "bar"}})
    assert isinstance(m.nested, dict)
    assert m.nested["hello"].foo == "bar"

    # mismatched types
    m = NestedModel.construct(nested={"hello": False})
    assert cast(Any, m.nested["hello"]) is False


def test_unknown_fields() -> None:
    """
    Test that unknown fields provided during model construction are preserved and accessible, and included in serialization output.
    """
    m1 = BasicModel.construct(foo="foo", unknown=1)
    assert m1.foo == "foo"
    assert cast(Any, m1).unknown == 1

    m2 = BasicModel.construct(foo="foo", unknown={"foo_bar": True})
    assert m2.foo == "foo"
    assert cast(Any, m2).unknown == {"foo_bar": True}

    assert model_dump(m2) == {"foo": "foo", "unknown": {"foo_bar": True}}


def test_strict_validation_unknown_fields() -> None:
    """
    Test that unknown fields are preserved during strict validation and included in serialization output.
    """
    class Model(BaseModel):
        foo: str

    model = parse_obj(Model, dict(foo="hello!", user="Robert"))
    assert model.foo == "hello!"
    assert cast(Any, model).user == "Robert"

    assert model_dump(model) == {"foo": "hello!", "user": "Robert"}


def test_aliases() -> None:
    """
    Test that models handle field aliases correctly during construction, including with mismatched types.
    """
    class Model(BaseModel):
        my_field: int = Field(alias="myField")

    m = Model.construct(myField=1)
    assert m.my_field == 1

    # mismatched types
    m = Model.construct(myField={"hello": False})
    assert cast(Any, m.my_field) == {"hello": False}


def test_repr() -> None:
    """
    Test that the string and repr representations of BasicModel display the correct field values.
    """
    model = BasicModel(foo="bar")
    assert str(model) == "BasicModel(foo='bar')"
    assert repr(model) == "BasicModel(foo='bar')"


def test_repr_nested_model() -> None:
    """
    Test that the string and repr representations of a nested model display the correct structure and values.
    """
    class Child(BaseModel):
        name: str
        age: int

    class Parent(BaseModel):
        name: str
        child: Child

    model = Parent(name="Robert", child=Child(name="Foo", age=5))
    assert str(model) == "Parent(name='Robert', child=Child(name='Foo', age=5))"
    assert repr(model) == "Parent(name='Robert', child=Child(name='Foo', age=5))"


def test_optional_list() -> None:
    """
    Test construction of a model with an optional list of submodels, verifying handling of None, empty lists, and lists of dictionaries.
    """
    class Submodel(BaseModel):
        name: str

    class Model(BaseModel):
        items: Optional[List[Submodel]]

    m = Model.construct(items=None)
    assert m.items is None

    m = Model.construct(items=[])
    assert m.items == []

    m = Model.construct(items=[{"name": "Robert"}])
    assert m.items is not None
    assert len(m.items) == 1
    assert m.items[0].name == "Robert"


def test_nested_union_of_models() -> None:
    """
    Test that a model with a union field correctly constructs the appropriate submodel based on input data.
    """
    class Submodel1(BaseModel):
        bar: bool

    class Submodel2(BaseModel):
        thing: str

    class Model(BaseModel):
        foo: Union[Submodel1, Submodel2]

    m = Model.construct(foo={"thing": "hello"})
    assert isinstance(m.foo, Submodel2)
    assert m.foo.thing == "hello"


def test_nested_union_of_mixed_types() -> None:
    """
    Tests construction of a model with a union field accepting a submodel, a boolean literal, or a string literal.
    
    Verifies that the correct variant is selected for each input type when constructing the model.
    """
    class Submodel1(BaseModel):
        bar: bool

    class Model(BaseModel):
        foo: Union[Submodel1, Literal[True], Literal["CARD_HOLDER"]]

    m = Model.construct(foo=True)
    assert m.foo is True

    m = Model.construct(foo="CARD_HOLDER")
    assert m.foo == "CARD_HOLDER"

    m = Model.construct(foo={"bar": False})
    assert isinstance(m.foo, Submodel1)
    assert m.foo.bar is False


def test_nested_union_multiple_variants() -> None:
    """
    Test construction of a model with a union field containing multiple submodels and None.
    
    Verifies that the correct submodel or None is selected based on the input dictionary, and that default construction results in None for the union field.
    """
    class Submodel1(BaseModel):
        bar: bool

    class Submodel2(BaseModel):
        thing: str

    class Submodel3(BaseModel):
        foo: int

    class Model(BaseModel):
        foo: Union[Submodel1, Submodel2, None, Submodel3]

    m = Model.construct(foo={"thing": "hello"})
    assert isinstance(m.foo, Submodel2)
    assert m.foo.thing == "hello"

    m = Model.construct(foo=None)
    assert m.foo is None

    m = Model.construct()
    assert m.foo is None

    m = Model.construct(foo={"foo": "1"})
    assert isinstance(m.foo, Submodel3)
    assert m.foo.foo == 1


def test_nested_union_invalid_data() -> None:
    """
    Test construction of a model with a union field using invalid data types.
    
    Verifies that when constructing a model with a union field and invalid input, the resulting field value or variant selection depends on the Pydantic version. In Pydantic v2, the first union variant is chosen and fields are coerced as needed; in v1, the variant selection and coercion differ.
    """
    class Submodel1(BaseModel):
        level: int

    class Submodel2(BaseModel):
        name: str

    class Model(BaseModel):
        foo: Union[Submodel1, Submodel2]

    m = Model.construct(foo=True)
    assert cast(bool, m.foo) is True

    m = Model.construct(foo={"name": 3})
    if PYDANTIC_V2:
        assert isinstance(m.foo, Submodel1)
        assert m.foo.name == 3  # type: ignore
    else:
        assert isinstance(m.foo, Submodel2)
        assert m.foo.name == "3"


def test_list_of_unions() -> None:
    """
    Test that a model with a list of union types correctly constructs items as the appropriate submodel or preserves mismatched types.
    
    Verifies that each item in the list is instantiated as the correct submodel when matching, and that non-matching types are preserved as-is.
    """
    class Submodel1(BaseModel):
        level: int

    class Submodel2(BaseModel):
        name: str

    class Model(BaseModel):
        items: List[Union[Submodel1, Submodel2]]

    m = Model.construct(items=[{"level": 1}, {"name": "Robert"}])
    assert len(m.items) == 2
    assert isinstance(m.items[0], Submodel1)
    assert m.items[0].level == 1
    assert isinstance(m.items[1], Submodel2)
    assert m.items[1].name == "Robert"

    m = Model.construct(items=[{"level": -1}, 156])
    assert len(m.items) == 2
    assert isinstance(m.items[0], Submodel1)
    assert m.items[0].level == -1
    assert cast(Any, m.items[1]) == 156


def test_union_of_lists() -> None:
    """
    Test construction of a model with a field that is a union of lists of different submodels.
    
    Verifies that the model correctly handles lists containing entries matching different submodel types, as well as entries with completely mismatched types, when using the `construct` method.
    """
    class SubModel1(BaseModel):
        level: int

    class SubModel2(BaseModel):
        name: str

    class Model(BaseModel):
        items: Union[List[SubModel1], List[SubModel2]]

    # with one valid entry
    m = Model.construct(items=[{"name": "Robert"}])
    assert len(m.items) == 1
    assert isinstance(m.items[0], SubModel2)
    assert m.items[0].name == "Robert"

    # with two entries pointing to different types
    m = Model.construct(items=[{"level": 1}, {"name": "Robert"}])
    assert len(m.items) == 2
    assert isinstance(m.items[0], SubModel1)
    assert m.items[0].level == 1
    assert isinstance(m.items[1], SubModel1)
    assert cast(Any, m.items[1]).name == "Robert"

    # with two entries pointing to *completely* different types
    m = Model.construct(items=[{"level": -1}, 156])
    assert len(m.items) == 2
    assert isinstance(m.items[0], SubModel1)
    assert m.items[0].level == -1
    assert cast(Any, m.items[1]) == 156


def test_dict_of_union() -> None:
    """
    Tests that a model with a dictionary field containing a union of submodels correctly constructs each entry as the appropriate submodel type based on input data.
    """
    class SubModel1(BaseModel):
        name: str

    class SubModel2(BaseModel):
        foo: str

    class Model(BaseModel):
        data: Dict[str, Union[SubModel1, SubModel2]]

    m = Model.construct(data={"hello": {"name": "there"}, "foo": {"foo": "bar"}})
    assert len(list(m.data.keys())) == 2
    assert isinstance(m.data["hello"], SubModel1)
    assert m.data["hello"].name == "there"
    assert isinstance(m.data["foo"], SubModel2)
    assert m.data["foo"].foo == "bar"

    # TODO: test mismatched type


def test_double_nested_union() -> None:
    """
    Tests construction of a model with a dictionary of lists containing a union of submodels, verifying correct instantiation of each variant based on input data.
    """
    class SubModel1(BaseModel):
        name: str

    class SubModel2(BaseModel):
        bar: str

    class Model(BaseModel):
        data: Dict[str, List[Union[SubModel1, SubModel2]]]

    m = Model.construct(data={"foo": [{"bar": "baz"}, {"name": "Robert"}]})
    assert len(m.data["foo"]) == 2

    entry1 = m.data["foo"][0]
    assert isinstance(entry1, SubModel2)
    assert entry1.bar == "baz"

    entry2 = m.data["foo"][1]
    assert isinstance(entry2, SubModel1)
    assert entry2.name == "Robert"

    # TODO: test mismatched type


def test_union_of_dict() -> None:
    """
    Tests construction of a model with a field that is a union of dictionaries containing different submodels, verifying correct instantiation and type assignment for each dictionary entry.
    """
    class SubModel1(BaseModel):
        name: str

    class SubModel2(BaseModel):
        foo: str

    class Model(BaseModel):
        data: Union[Dict[str, SubModel1], Dict[str, SubModel2]]

    m = Model.construct(data={"hello": {"name": "there"}, "foo": {"foo": "bar"}})
    assert len(list(m.data.keys())) == 2
    assert isinstance(m.data["hello"], SubModel1)
    assert m.data["hello"].name == "there"
    assert isinstance(m.data["foo"], SubModel1)
    assert cast(Any, m.data["foo"]).foo == "bar"


def test_iso8601_datetime() -> None:
    """
    Tests that ISO8601 datetime strings are correctly parsed into datetime objects and serialized to JSON with the expected formatting, accounting for differences between Pydantic v1 and v2.
    """
    class Model(BaseModel):
        created_at: datetime

    expected = datetime(2019, 12, 27, 18, 11, 19, 117000, tzinfo=timezone.utc)

    if PYDANTIC_V2:
        expected_json = '{"created_at":"2019-12-27T18:11:19.117000Z"}'
    else:
        expected_json = '{"created_at": "2019-12-27T18:11:19.117000+00:00"}'

    model = Model.construct(created_at="2019-12-27T18:11:19.117Z")
    assert model.created_at == expected
    assert model_json(model) == expected_json

    model = parse_obj(Model, dict(created_at="2019-12-27T18:11:19.117Z"))
    assert model.created_at == expected
    assert model_json(model) == expected_json


def test_does_not_coerce_int() -> None:
    """
    Verify that the model's integer field preserves the original type when constructed with non-integer values, without coercion.
    """
    class Model(BaseModel):
        bar: int

    assert Model.construct(bar=1).bar == 1
    assert Model.construct(bar=10.9).bar == 10.9
    assert Model.construct(bar="19").bar == "19"  # type: ignore[comparison-overlap]
    assert Model.construct(bar=False).bar is False


def test_int_to_float_safe_conversion() -> None:
    """
    Test that integer values are safely converted to float when possible, and large integers remain as int to avoid precision loss.
    """
    class Model(BaseModel):
        float_field: float

    m = Model.construct(float_field=10)
    assert m.float_field == 10.0
    assert isinstance(m.float_field, float)

    m = Model.construct(float_field=10.12)
    assert m.float_field == 10.12
    assert isinstance(m.float_field, float)

    # number too big
    m = Model.construct(float_field=2**53 + 1)
    assert m.float_field == 2**53 + 1
    assert isinstance(m.float_field, int)


def test_deprecated_alias() -> None:
    """
    Test that a deprecated alias property correctly forwards to the underlying field and maintains value consistency when constructing or parsing the model.
    """
    class Model(BaseModel):
        resource_id: str = Field(alias="model_id")

        @property
        def model_id(self) -> str:
            return self.resource_id

    m = Model.construct(model_id="id")
    assert m.model_id == "id"
    assert m.resource_id == "id"
    assert m.resource_id is m.model_id

    m = parse_obj(Model, {"model_id": "id"})
    assert m.model_id == "id"
    assert m.resource_id == "id"
    assert m.resource_id is m.model_id


def test_omitted_fields() -> None:
    """
    Test that omitted optional fields are not included in the model's field set, while explicitly set fields are tracked.
    """
    class Model(BaseModel):
        resource_id: Optional[str] = None

    m = Model.construct()
    assert m.resource_id is None
    assert "resource_id" not in m.model_fields_set

    m = Model.construct(resource_id=None)
    assert m.resource_id is None
    assert "resource_id" in m.model_fields_set

    m = Model.construct(resource_id="foo")
    assert m.resource_id == "foo"
    assert "resource_id" in m.model_fields_set


def test_to_dict() -> None:
    """
    Test the `to_dict` method of custom models for correct serialization behavior.
    
    Verifies that `to_dict` correctly handles field aliases, unset and None values, exclusion options, and datetime serialization modes. Also checks error handling for unsupported parameters in Pydantic v1.
    """
    class Model(BaseModel):
        foo: Optional[str] = Field(alias="FOO", default=None)

    m = Model(FOO="hello")
    assert m.to_dict() == {"FOO": "hello"}
    assert m.to_dict(use_api_names=False) == {"foo": "hello"}

    m2 = Model()
    assert m2.to_dict() == {}
    assert m2.to_dict(exclude_unset=False) == {"FOO": None}
    assert m2.to_dict(exclude_unset=False, exclude_none=True) == {}
    assert m2.to_dict(exclude_unset=False, exclude_defaults=True) == {}

    m3 = Model(FOO=None)
    assert m3.to_dict() == {"FOO": None}
    assert m3.to_dict(exclude_none=True) == {}
    assert m3.to_dict(exclude_defaults=True) == {}

    class Model2(BaseModel):
        created_at: datetime

    time_str = "2024-03-21T11:39:01.275859"
    m4 = Model2.construct(created_at=time_str)
    assert m4.to_dict(mode="python") == {"created_at": datetime.fromisoformat(time_str)}
    assert m4.to_dict(mode="json") == {"created_at": time_str}

    if not PYDANTIC_V2:
        with pytest.raises(ValueError, match="warnings is only supported in Pydantic v2"):
            m.to_dict(warnings=False)


def test_forwards_compat_model_dump_method() -> None:
    """
    Test the `model_dump` method for forward compatibility across Pydantic versions.
    
    Verifies correct serialization output with various options such as field inclusion, exclusion, alias usage, and exclusion of unset, none, or default values. Also checks that unsupported parameters raise appropriate errors in Pydantic v1.
    """
    class Model(BaseModel):
        foo: Optional[str] = Field(alias="FOO", default=None)

    m = Model(FOO="hello")
    assert m.model_dump() == {"foo": "hello"}
    assert m.model_dump(include={"bar"}) == {}
    assert m.model_dump(exclude={"foo"}) == {}
    assert m.model_dump(by_alias=True) == {"FOO": "hello"}

    m2 = Model()
    assert m2.model_dump() == {"foo": None}
    assert m2.model_dump(exclude_unset=True) == {}
    assert m2.model_dump(exclude_none=True) == {}
    assert m2.model_dump(exclude_defaults=True) == {}

    m3 = Model(FOO=None)
    assert m3.model_dump() == {"foo": None}
    assert m3.model_dump(exclude_none=True) == {}

    if not PYDANTIC_V2:
        with pytest.raises(ValueError, match="round_trip is only supported in Pydantic v2"):
            m.model_dump(round_trip=True)

        with pytest.raises(ValueError, match="warnings is only supported in Pydantic v2"):
            m.model_dump(warnings=False)


def test_compat_method_no_error_for_warnings() -> None:
    """
    Verify that calling `model_dump` with `warnings=False` does not raise an error and returns a dictionary.
    """
    class Model(BaseModel):
        foo: Optional[str]

    m = Model(foo="hello")
    assert isinstance(model_dump(m, warnings=False), dict)


def test_to_json() -> None:
    """
    Test the `to_json` method of a model for correct JSON serialization with various options.
    
    Verifies that field aliases, unset and None exclusion, default exclusion, and indentation are handled as expected. Also checks error handling for unsupported parameters in Pydantic v1.
    """
    class Model(BaseModel):
        foo: Optional[str] = Field(alias="FOO", default=None)

    m = Model(FOO="hello")
    assert json.loads(m.to_json()) == {"FOO": "hello"}
    assert json.loads(m.to_json(use_api_names=False)) == {"foo": "hello"}

    if PYDANTIC_V2:
        assert m.to_json(indent=None) == '{"FOO":"hello"}'
    else:
        assert m.to_json(indent=None) == '{"FOO": "hello"}'

    m2 = Model()
    assert json.loads(m2.to_json()) == {}
    assert json.loads(m2.to_json(exclude_unset=False)) == {"FOO": None}
    assert json.loads(m2.to_json(exclude_unset=False, exclude_none=True)) == {}
    assert json.loads(m2.to_json(exclude_unset=False, exclude_defaults=True)) == {}

    m3 = Model(FOO=None)
    assert json.loads(m3.to_json()) == {"FOO": None}
    assert json.loads(m3.to_json(exclude_none=True)) == {}

    if not PYDANTIC_V2:
        with pytest.raises(ValueError, match="warnings is only supported in Pydantic v2"):
            m.to_json(warnings=False)


def test_forwards_compat_model_dump_json_method() -> None:
    """
    Test the `model_dump_json` method for correct JSON serialization and option handling.
    
    Verifies that the method serializes model instances to JSON with various options, including field inclusion, alias usage, indentation, and exclusion of unset, none, or default values. Also checks that unsupported options raise errors in Pydantic v1.
    """
    class Model(BaseModel):
        foo: Optional[str] = Field(alias="FOO", default=None)

    m = Model(FOO="hello")
    assert json.loads(m.model_dump_json()) == {"foo": "hello"}
    assert json.loads(m.model_dump_json(include={"bar"})) == {}
    assert json.loads(m.model_dump_json(include={"foo"})) == {"foo": "hello"}
    assert json.loads(m.model_dump_json(by_alias=True)) == {"FOO": "hello"}

    assert m.model_dump_json(indent=2) == '{\n  "foo": "hello"\n}'

    m2 = Model()
    assert json.loads(m2.model_dump_json()) == {"foo": None}
    assert json.loads(m2.model_dump_json(exclude_unset=True)) == {}
    assert json.loads(m2.model_dump_json(exclude_none=True)) == {}
    assert json.loads(m2.model_dump_json(exclude_defaults=True)) == {}

    m3 = Model(FOO=None)
    assert json.loads(m3.model_dump_json()) == {"foo": None}
    assert json.loads(m3.model_dump_json(exclude_none=True)) == {}

    if not PYDANTIC_V2:
        with pytest.raises(ValueError, match="round_trip is only supported in Pydantic v2"):
            m.model_dump_json(round_trip=True)

        with pytest.raises(ValueError, match="warnings is only supported in Pydantic v2"):
            m.model_dump_json(warnings=False)


def test_type_compat() -> None:
    # our model type can be assigned to Pydantic's model type

    """
    Verify that the custom BaseModel type is compatible with Pydantic's BaseModel type.
    """
    def takes_pydantic(model: pydantic.BaseModel) -> None:  # noqa: ARG001
        ...

    class OurModel(BaseModel):
        foo: Optional[str] = None

    takes_pydantic(OurModel())


def test_annotated_types() -> None:
    """
    Test that models wrapped in Annotated types are correctly constructed and retain their field values.
    """
    class Model(BaseModel):
        value: str

    m = construct_type(
        value={"value": "foo"},
        type_=cast(Any, Annotated[Model, "random metadata"]),
    )
    assert isinstance(m, Model)
    assert m.value == "foo"


def test_discriminated_unions_invalid_data() -> None:
    """
    Test discriminated union construction with invalid data types for variant fields.
    
    Verifies that when constructing a discriminated union of models with a discriminator field, the correct variant is selected even if the data type of a field does not match the expected type. Checks that the field value is preserved as-is or coerced according to the Pydantic version.
    """
    class A(BaseModel):
        type: Literal["a"]

        data: str

    class B(BaseModel):
        type: Literal["b"]

        data: int

    m = construct_type(
        value={"type": "b", "data": "foo"},
        type_=cast(Any, Annotated[Union[A, B], PropertyInfo(discriminator="type")]),
    )
    assert isinstance(m, B)
    assert m.type == "b"
    assert m.data == "foo"  # type: ignore[comparison-overlap]

    m = construct_type(
        value={"type": "a", "data": 100},
        type_=cast(Any, Annotated[Union[A, B], PropertyInfo(discriminator="type")]),
    )
    assert isinstance(m, A)
    assert m.type == "a"
    if PYDANTIC_V2:
        assert m.data == 100  # type: ignore[comparison-overlap]
    else:
        # pydantic v1 automatically converts inputs to strings
        # if the expected type is a str
        assert m.data == "100"


def test_discriminated_unions_unknown_variant() -> None:
    """
    Test that constructing a discriminated union with an unknown discriminator value selects the first variant and preserves unknown fields.
    
    Verifies that when the discriminator field value does not match any known variant, the first variant is chosen, the unknown discriminator value is assigned, and additional fields are retained.
    """
    class A(BaseModel):
        type: Literal["a"]

        data: str

    class B(BaseModel):
        type: Literal["b"]

        data: int

    m = construct_type(
        value={"type": "c", "data": None, "new_thing": "bar"},
        type_=cast(Any, Annotated[Union[A, B], PropertyInfo(discriminator="type")]),
    )

    # just chooses the first variant
    assert isinstance(m, A)
    assert m.type == "c"  # type: ignore[comparison-overlap]
    assert m.data == None  # type: ignore[unreachable]
    assert m.new_thing == "bar"


def test_discriminated_unions_invalid_data_nested_unions() -> None:
    """
    Tests construction of nested discriminated unions with invalid data, verifying that the correct variant is selected and that field values are preserved even when types do not match the model definition.
    """
    class A(BaseModel):
        type: Literal["a"]

        data: str

    class B(BaseModel):
        type: Literal["b"]

        data: int

    class C(BaseModel):
        type: Literal["c"]

        data: bool

    m = construct_type(
        value={"type": "b", "data": "foo"},
        type_=cast(Any, Annotated[Union[Union[A, B], C], PropertyInfo(discriminator="type")]),
    )
    assert isinstance(m, B)
    assert m.type == "b"
    assert m.data == "foo"  # type: ignore[comparison-overlap]

    m = construct_type(
        value={"type": "c", "data": "foo"},
        type_=cast(Any, Annotated[Union[Union[A, B], C], PropertyInfo(discriminator="type")]),
    )
    assert isinstance(m, C)
    assert m.type == "c"
    assert m.data == "foo"  # type: ignore[comparison-overlap]


def test_discriminated_unions_with_aliases_invalid_data() -> None:
    """
    Tests discriminated unions with discriminator fields that use aliases, verifying correct variant selection and type coercion when input data does not match the expected type.
    """
    class A(BaseModel):
        foo_type: Literal["a"] = Field(alias="type")

        data: str

    class B(BaseModel):
        foo_type: Literal["b"] = Field(alias="type")

        data: int

    m = construct_type(
        value={"type": "b", "data": "foo"},
        type_=cast(Any, Annotated[Union[A, B], PropertyInfo(discriminator="foo_type")]),
    )
    assert isinstance(m, B)
    assert m.foo_type == "b"
    assert m.data == "foo"  # type: ignore[comparison-overlap]

    m = construct_type(
        value={"type": "a", "data": 100},
        type_=cast(Any, Annotated[Union[A, B], PropertyInfo(discriminator="foo_type")]),
    )
    assert isinstance(m, A)
    assert m.foo_type == "a"
    if PYDANTIC_V2:
        assert m.data == 100  # type: ignore[comparison-overlap]
    else:
        # pydantic v1 automatically converts inputs to strings
        # if the expected type is a str
        assert m.data == "100"


def test_discriminated_unions_overlapping_discriminators_invalid_data() -> None:
    """
    Tests discriminated unions with overlapping discriminator values and invalid data.
    
    Verifies that when multiple union variants share the same discriminator value, the first matching variant is selected, and invalid field data is preserved without coercion.
    """
    class A(BaseModel):
        type: Literal["a"]

        data: bool

    class B(BaseModel):
        type: Literal["a"]

        data: int

    m = construct_type(
        value={"type": "a", "data": "foo"},
        type_=cast(Any, Annotated[Union[A, B], PropertyInfo(discriminator="type")]),
    )
    assert isinstance(m, B)
    assert m.type == "a"
    assert m.data == "foo"  # type: ignore[comparison-overlap]


def test_discriminated_unions_invalid_data_uses_cache() -> None:
    """
    Test that discriminated union metadata is cached and reused during repeated model construction with invalid data.
    
    Verifies that the discriminator details for a union of models are stored on the union type after the first construction, and that subsequent constructions reuse the cached discriminator metadata, even when input data does not match the expected type.
    """
    class A(BaseModel):
        type: Literal["a"]

        data: str

    class B(BaseModel):
        type: Literal["b"]

        data: int

    UnionType = cast(Any, Union[A, B])

    assert not hasattr(UnionType, "__discriminator__")

    m = construct_type(
        value={"type": "b", "data": "foo"}, type_=cast(Any, Annotated[UnionType, PropertyInfo(discriminator="type")])
    )
    assert isinstance(m, B)
    assert m.type == "b"
    assert m.data == "foo"  # type: ignore[comparison-overlap]

    discriminator = UnionType.__discriminator__
    assert discriminator is not None

    m = construct_type(
        value={"type": "b", "data": "foo"}, type_=cast(Any, Annotated[UnionType, PropertyInfo(discriminator="type")])
    )
    assert isinstance(m, B)
    assert m.type == "b"
    assert m.data == "foo"  # type: ignore[comparison-overlap]

    # if the discriminator details object stays the same between invocations then
    # we hit the cache
    assert UnionType.__discriminator__ is discriminator


@pytest.mark.skipif(not PYDANTIC_V2, reason="TypeAliasType is not supported in Pydantic v1")
def test_type_alias_type() -> None:
    """
    Tests that models using TypeAliasType fields are constructed correctly, ensuring type aliasing and unions with aliases are handled as expected.
    """
    Alias = TypeAliasType("Alias", str)  # pyright: ignore

    class Model(BaseModel):
        alias: Alias
        union: Union[int, Alias]

    m = construct_type(value={"alias": "foo", "union": "bar"}, type_=Model)
    assert isinstance(m, Model)
    assert isinstance(m.alias, str)
    assert m.alias == "foo"
    assert isinstance(m.union, str)
    assert m.union == "bar"


@pytest.mark.skipif(not PYDANTIC_V2, reason="TypeAliasType is not supported in Pydantic v1")
def test_field_named_cls() -> None:
    """
    Test that a model with a field named 'cls' can be constructed and its value is correctly set as a string.
    """
    class Model(BaseModel):
        cls: str

    m = construct_type(value={"cls": "foo"}, type_=Model)
    assert isinstance(m, Model)
    assert isinstance(m.cls, str)


def test_discriminated_union_case() -> None:
    """
    Tests discriminated union construction where input data matches a nested variant but is missing required fields, ensuring the correct variant is selected and constructed.
    """
    class A(BaseModel):
        type: Literal["a"]

        data: bool

    class B(BaseModel):
        type: Literal["b"]

        data: List[Union[A, object]]

    class ModelA(BaseModel):
        type: Literal["modelA"]

        data: int

    class ModelB(BaseModel):
        type: Literal["modelB"]

        required: str

        data: Union[A, B]

    # when constructing ModelA | ModelB, value data doesn't match ModelB exactly - missing `required`
    m = construct_type(
        value={"type": "modelB", "data": {"type": "a", "data": True}},
        type_=cast(Any, Annotated[Union[ModelA, ModelB], PropertyInfo(discriminator="type")]),
    )

    assert isinstance(m, ModelB)
