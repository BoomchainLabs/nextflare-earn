from __future__ import annotations

import os
import inspect
from typing import TYPE_CHECKING, Any, Type, Union, Generic, TypeVar, Callable, cast
from datetime import date, datetime
from typing_extensions import (
    Unpack,
    Literal,
    ClassVar,
    Protocol,
    Required,
    ParamSpec,
    TypedDict,
    TypeGuard,
    final,
    override,
    runtime_checkable,
)

import pydantic
from pydantic.fields import FieldInfo

from ._types import (
    Body,
    IncEx,
    Query,
    ModelT,
    Headers,
    Timeout,
    NotGiven,
    AnyMapping,
    HttpxRequestFiles,
)
from ._utils import (
    PropertyInfo,
    is_list,
    is_given,
    json_safe,
    lru_cache,
    is_mapping,
    parse_date,
    coerce_boolean,
    parse_datetime,
    strip_not_given,
    extract_type_arg,
    is_annotated_type,
    is_type_alias_type,
    strip_annotated_type,
)
from ._compat import (
    PYDANTIC_V2,
    ConfigDict,
    GenericModel as BaseGenericModel,
    get_args,
    is_union,
    parse_obj,
    get_origin,
    is_literal_type,
    get_model_config,
    get_model_fields,
    field_get_default,
)
from ._constants import RAW_RESPONSE_HEADER

if TYPE_CHECKING:
    from pydantic_core.core_schema import ModelField, ModelSchema, LiteralSchema, ModelFieldsSchema

__all__ = ["BaseModel", "GenericModel"]

_T = TypeVar("_T")
_BaseModelT = TypeVar("_BaseModelT", bound="BaseModel")

P = ParamSpec("P")


@runtime_checkable
class _ConfigProtocol(Protocol):
    allow_population_by_field_name: bool


class BaseModel(pydantic.BaseModel):
    if PYDANTIC_V2:
        model_config: ClassVar[ConfigDict] = ConfigDict(
            extra="allow", defer_build=coerce_boolean(os.environ.get("DEFER_PYDANTIC_BUILD", "true"))
        )
    else:

        @property
        @override
        def model_fields_set(self) -> set[str]:
            # a forwards-compat shim for pydantic v2
            """
            Return the set of field names that have been explicitly set on this model instance.
            """
            return self.__fields_set__  # type: ignore

        class Config(pydantic.BaseConfig):  # pyright: ignore[reportDeprecated]
            extra: Any = pydantic.Extra.allow  # type: ignore

    def to_dict(
        self,
        *,
        mode: Literal["json", "python"] = "python",
        use_api_names: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        warnings: bool = True,
    ) -> dict[str, object]:
        """
        Return a dictionary representation of the model, with options for field inclusion, naming, and serialization mode.
        
        Parameters:
            mode (Literal["json", "python"]): Output mode; "json" ensures all values are JSON serializable, while "python" preserves native Python types.
            use_api_names (bool): If True, uses API field names (aliases) as keys; if False, uses model property names.
            exclude_unset (bool): If True, omits fields that were not explicitly set.
            exclude_defaults (bool): If True, omits fields set to their default value.
            exclude_none (bool): If True, omits fields with a value of None.
            warnings (bool): If True, enables warnings for invalid fields (Pydantic v2 only).
        
        Returns:
            dict[str, object]: Dictionary representation of the model according to the specified options.
        """
        return self.model_dump(
            mode=mode,
            by_alias=use_api_names,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            warnings=warnings,
        )

    def to_json(
        self,
        *,
        indent: int | None = 2,
        use_api_names: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        warnings: bool = True,
    ) -> str:
        """
        Return a JSON string representation of the model, formatted for API communication.
        
        By default, only explicitly set fields are included, and field names use API aliases. Options allow customization of indentation, field inclusion, and warning display (Pydantic v2 only).
        
        Parameters:
            indent (int | None): Number of spaces for indentation in the output, or `None` for compact JSON.
            use_api_names (bool): If True, use API field names (aliases) instead of model property names.
            exclude_unset (bool): If True, omit fields that were not explicitly set.
            exclude_defaults (bool): If True, omit fields with default values.
            exclude_none (bool): If True, omit fields with a value of `None`.
            warnings (bool): If True, display serialization warnings (Pydantic v2 only).
        
        Returns:
            str: The JSON string representation of the model.
        """
        return self.model_dump_json(
            indent=indent,
            by_alias=use_api_names,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            warnings=warnings,
        )

    @override
    def __str__(self) -> str:
        # mypy complains about an invalid self arg
        """
        Return a concise string representation of the model instance, including its class name and field values.
        """
        return f"{self.__repr_name__()}({self.__repr_str__(', ')})"  # type: ignore[misc]

    # Override the 'construct' method in a way that supports recursive parsing without validation.
    # Based on https://github.com/samuelcolvin/pydantic/issues/1168#issuecomment-817742836.
    @classmethod
    @override
    def construct(  # pyright: ignore[reportIncompatibleMethodOverride]
        __cls: Type[ModelT],
        _fields_set: set[str] | None = None,
        **values: object,
    ) -> ModelT:
        """
        Create a model instance without validation, recursively constructing nested fields and handling extra attributes.
        
        Parameters:
            _fields_set (set[str] | None): Optional set of field names considered set on the model. If not provided, an empty set is used.
        
        Returns:
            ModelT: An instance of the model with fields populated from the provided values, constructed without validation.
        """
        m = __cls.__new__(__cls)
        fields_values: dict[str, object] = {}

        config = get_model_config(__cls)
        populate_by_name = (
            config.allow_population_by_field_name
            if isinstance(config, _ConfigProtocol)
            else config.get("populate_by_name")
        )

        if _fields_set is None:
            _fields_set = set()

        model_fields = get_model_fields(__cls)
        for name, field in model_fields.items():
            key = field.alias
            if key is None or (key not in values and populate_by_name):
                key = name

            if key in values:
                fields_values[name] = _construct_field(value=values[key], field=field, key=key)
                _fields_set.add(name)
            else:
                fields_values[name] = field_get_default(field)

        _extra = {}
        for key, value in values.items():
            if key not in model_fields:
                if PYDANTIC_V2:
                    _extra[key] = value
                else:
                    _fields_set.add(key)
                    fields_values[key] = value

        object.__setattr__(m, "__dict__", fields_values)

        if PYDANTIC_V2:
            # these properties are copied from Pydantic's `model_construct()` method
            object.__setattr__(m, "__pydantic_private__", None)
            object.__setattr__(m, "__pydantic_extra__", _extra)
            object.__setattr__(m, "__pydantic_fields_set__", _fields_set)
        else:
            # init_private_attributes() does not exist in v2
            m._init_private_attributes()  # type: ignore

            # copied from Pydantic v1's `construct()` method
            object.__setattr__(m, "__fields_set__", _fields_set)

        return m

    if not TYPE_CHECKING:
        # type checkers incorrectly complain about this assignment
        # because the type signatures are technically different
        # although not in practice
        model_construct = construct

    if not PYDANTIC_V2:
        # we define aliases for some of the new pydantic v2 methods so
        # that we can just document these methods without having to specify
        # a specific pydantic version as some users may not know which
        # pydantic version they are currently using

        @override
        def model_dump(
            self,
            *,
            mode: Literal["json", "python"] | str = "python",
            include: IncEx | None = None,
            exclude: IncEx | None = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            round_trip: bool = False,
            warnings: bool | Literal["none", "warn", "error"] = True,
            context: dict[str, Any] | None = None,
            serialize_as_any: bool = False,
        ) -> dict[str, Any]:
            """
            Generate a dictionary representation of the model, with options for JSON or Python-native types and field inclusion or exclusion.
            
            Parameters:
                mode (str): Output mode; "json" for JSON-serializable types, "python" for native Python types.
                include: Fields to include in the output.
                exclude: Fields to exclude from the output.
                by_alias (bool): Use field aliases as keys if defined.
                exclude_unset (bool): Exclude fields that are unset or None.
                exclude_defaults (bool): Exclude fields set to their default value.
                exclude_none (bool): Exclude fields with a value of None.
            
            Returns:
                dict[str, Any]: Dictionary representation of the model.
            """
            if mode not in {"json", "python"}:
                raise ValueError("mode must be either 'json' or 'python'")
            if round_trip != False:
                raise ValueError("round_trip is only supported in Pydantic v2")
            if warnings != True:
                raise ValueError("warnings is only supported in Pydantic v2")
            if context is not None:
                raise ValueError("context is only supported in Pydantic v2")
            if serialize_as_any != False:
                raise ValueError("serialize_as_any is only supported in Pydantic v2")
            dumped = super().dict(  # pyright: ignore[reportDeprecated]
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )

            return cast(dict[str, Any], json_safe(dumped)) if mode == "json" else dumped

        @override
        def model_dump_json(
            self,
            *,
            indent: int | None = None,
            include: IncEx | None = None,
            exclude: IncEx | None = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            round_trip: bool = False,
            warnings: bool | Literal["none", "warn", "error"] = True,
            context: dict[str, Any] | None = None,
            serialize_as_any: bool = False,
        ) -> str:
            """
            Return a JSON string representation of the model, with options to control field inclusion, exclusion, alias usage, and formatting.
            
            Parameters:
                indent (int | None): Number of spaces for indentation in the output, or None for compact output.
                include (IncEx | None): Fields to include in the output.
                exclude (IncEx | None): Fields to exclude from the output.
                by_alias (bool): Whether to use field aliases in the output.
                exclude_unset (bool): Exclude fields that were not explicitly set.
                exclude_defaults (bool): Exclude fields with default values.
                exclude_none (bool): Exclude fields with a value of None.
            
            Returns:
                str: The JSON string representation of the model.
            """
            if round_trip != False:
                raise ValueError("round_trip is only supported in Pydantic v2")
            if warnings != True:
                raise ValueError("warnings is only supported in Pydantic v2")
            if context is not None:
                raise ValueError("context is only supported in Pydantic v2")
            if serialize_as_any != False:
                raise ValueError("serialize_as_any is only supported in Pydantic v2")
            return super().json(  # type: ignore[reportDeprecated]
                indent=indent,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )


def _construct_field(value: object, field: FieldInfo, key: str) -> object:
    """
    Coerces a value to the expected type for a Pydantic model field, using the field's type annotation.
    
    If the value is `None`, returns the field's default value. Raises a `RuntimeError` if the field's type annotation is missing.
    """
    if value is None:
        return field_get_default(field)

    if PYDANTIC_V2:
        type_ = field.annotation
    else:
        type_ = cast(type, field.outer_type_)  # type: ignore

    if type_ is None:
        raise RuntimeError(f"Unexpected field type is None for {key}")

    return construct_type(value=value, type_=type_)


def is_basemodel(type_: type) -> bool:
    """
    Determine if the given type is a subclass of BaseModel or a union containing any BaseModel subclass.
    
    Returns:
        bool: True if the type is a BaseModel subclass or a union with at least one BaseModel variant; otherwise, False.
    """
    if is_union(type_):
        for variant in get_args(type_):
            if is_basemodel(variant):
                return True

        return False

    return is_basemodel_type(type_)


def is_basemodel_type(type_: type) -> TypeGuard[type[BaseModel] | type[GenericModel]]:
    """
    Determine if the given type is a subclass of BaseModel or GenericModel.
    
    Returns:
        TypeGuard[type[BaseModel] | type[GenericModel]]: True if the type is a subclass of BaseModel or GenericModel, otherwise False.
    """
    origin = get_origin(type_) or type_
    if not inspect.isclass(origin):
        return False
    return issubclass(origin, BaseModel) or issubclass(origin, GenericModel)


def build(
    base_model_cls: Callable[P, _BaseModelT],
    *args: P.args,
    **kwargs: P.kwargs,
) -> _BaseModelT:
    """
    Instantiate a BaseModel subclass without validation using keyword arguments only.
    
    Raises:
        TypeError: If any positional arguments are provided.
    
    Returns:
        An instance of the specified BaseModel subclass with fields populated from the provided keyword arguments.
    """
    if args:
        raise TypeError(
            "Received positional arguments which are not supported; Keyword arguments must be used instead",
        )

    return cast(_BaseModelT, construct_type(type_=base_model_cls, value=kwargs))


def construct_type_unchecked(*, value: object, type_: type[_T]) -> _T:
    """
    Coerces a value to the specified type, constructing nested values as needed, without strict type guarantees.
    
    Parameters:
        value (object): The input value to coerce.
        type_ (type[_T]): The target type for coercion.
    
    Returns:
        _T: The coerced value, which may not strictly match the target type.
    """
    return cast(_T, construct_type(value=value, type_=type_))


def construct_type(*, value: object, type_: object) -> object:
    """
    Recursively coerces a value to the specified type, constructing nested models and handling unions, generics, and common built-in types.
    
    Attempts to convert the input value to the target type, supporting:
    - Unwrapping of type aliases and annotated types.
    - Discriminated and regular unions, resolving the correct variant when possible.
    - Recursive construction of dictionaries, lists, and Pydantic models.
    - Coercion of integers to floats when appropriate.
    - Parsing of datetime and date values.
    
    If coercion is not possible, returns the original value unchanged.
    """

    # store a reference to the original type we were given before we extract any inner
    # types so that we can properly resolve forward references in `TypeAliasType` annotations
    original_type = None

    # we allow `object` as the input type because otherwise, passing things like
    # `Literal['value']` will be reported as a type error by type checkers
    type_ = cast("type[object]", type_)
    if is_type_alias_type(type_):
        original_type = type_  # type: ignore[unreachable]
        type_ = type_.__value__  # type: ignore[unreachable]

    # unwrap `Annotated[T, ...]` -> `T`
    if is_annotated_type(type_):
        meta: tuple[Any, ...] = get_args(type_)[1:]
        type_ = extract_type_arg(type_, 0)
    else:
        meta = tuple()

    # we need to use the origin class for any types that are subscripted generics
    # e.g. Dict[str, object]
    origin = get_origin(type_) or type_
    args = get_args(type_)

    if is_union(origin):
        try:
            return validate_type(type_=cast("type[object]", original_type or type_), value=value)
        except Exception:
            pass

        # if the type is a discriminated union then we want to construct the right variant
        # in the union, even if the data doesn't match exactly, otherwise we'd break code
        # that relies on the constructed class types, e.g.
        #
        # class FooType:
        #   kind: Literal['foo']
        #   value: str
        #
        # class BarType:
        #   kind: Literal['bar']
        #   value: int
        #
        # without this block, if the data we get is something like `{'kind': 'bar', 'value': 'foo'}` then
        # we'd end up constructing `FooType` when it should be `BarType`.
        discriminator = _build_discriminated_union_meta(union=type_, meta_annotations=meta)
        if discriminator and is_mapping(value):
            variant_value = value.get(discriminator.field_alias_from or discriminator.field_name)
            if variant_value and isinstance(variant_value, str):
                variant_type = discriminator.mapping.get(variant_value)
                if variant_type:
                    return construct_type(type_=variant_type, value=value)

        # if the data is not valid, use the first variant that doesn't fail while deserializing
        for variant in args:
            try:
                return construct_type(value=value, type_=variant)
            except Exception:
                continue

        raise RuntimeError(f"Could not convert data into a valid instance of {type_}")

    if origin == dict:
        if not is_mapping(value):
            return value

        _, items_type = get_args(type_)  # Dict[_, items_type]
        return {key: construct_type(value=item, type_=items_type) for key, item in value.items()}

    if (
        not is_literal_type(type_)
        and inspect.isclass(origin)
        and (issubclass(origin, BaseModel) or issubclass(origin, GenericModel))
    ):
        if is_list(value):
            return [cast(Any, type_).construct(**entry) if is_mapping(entry) else entry for entry in value]

        if is_mapping(value):
            if issubclass(type_, BaseModel):
                return type_.construct(**value)  # type: ignore[arg-type]

            return cast(Any, type_).construct(**value)

    if origin == list:
        if not is_list(value):
            return value

        inner_type = args[0]  # List[inner_type]
        return [construct_type(value=entry, type_=inner_type) for entry in value]

    if origin == float:
        if isinstance(value, int):
            coerced = float(value)
            if coerced != value:
                return value
            return coerced

        return value

    if type_ == datetime:
        try:
            return parse_datetime(value)  # type: ignore
        except Exception:
            return value

    if type_ == date:
        try:
            return parse_date(value)  # type: ignore
        except Exception:
            return value

    return value


@runtime_checkable
class CachedDiscriminatorType(Protocol):
    __discriminator__: DiscriminatorDetails


class DiscriminatorDetails:
    field_name: str
    """The name of the discriminator field in the variant class, e.g.

    ```py
    class Foo(BaseModel):
        type: Literal['foo']
    ```

    Will result in field_name='type'
    """

    field_alias_from: str | None
    """The name of the discriminator field in the API response, e.g.

    ```py
    class Foo(BaseModel):
        type: Literal['foo'] = Field(alias='type_from_api')
    ```

    Will result in field_alias_from='type_from_api'
    """

    mapping: dict[str, type]
    """Mapping of discriminator value to variant type, e.g.

    {'foo': FooVariant, 'bar': BarVariant}
    """

    def __init__(
        self,
        *,
        mapping: dict[str, type],
        discriminator_field: str,
        discriminator_alias: str | None,
    ) -> None:
        """
        Initialize DiscriminatorDetails with a mapping of discriminator values to types and discriminator field information.
        
        Parameters:
            mapping (dict[str, type]): Maps discriminator values to their corresponding variant types.
            discriminator_field (str): The name of the discriminator field used to distinguish variants.
            discriminator_alias (str | None): An optional alias for the discriminator field.
        """
        self.mapping = mapping
        self.field_name = discriminator_field
        self.field_alias_from = discriminator_alias


def _build_discriminated_union_meta(*, union: type, meta_annotations: tuple[Any, ...]) -> DiscriminatorDetails | None:
    """
    Builds and caches discriminator metadata for a discriminated union type.
    
    Inspects the provided union type and its annotations to extract the discriminator field name, its alias (if any), and a mapping from discriminator values to their corresponding variant types. Returns a `DiscriminatorDetails` object if a discriminator is found; otherwise, returns `None`.
    """
    if isinstance(union, CachedDiscriminatorType):
        return union.__discriminator__

    discriminator_field_name: str | None = None

    for annotation in meta_annotations:
        if isinstance(annotation, PropertyInfo) and annotation.discriminator is not None:
            discriminator_field_name = annotation.discriminator
            break

    if not discriminator_field_name:
        return None

    mapping: dict[str, type] = {}
    discriminator_alias: str | None = None

    for variant in get_args(union):
        variant = strip_annotated_type(variant)
        if is_basemodel_type(variant):
            if PYDANTIC_V2:
                field = _extract_field_schema_pv2(variant, discriminator_field_name)
                if not field:
                    continue

                # Note: if one variant defines an alias then they all should
                discriminator_alias = field.get("serialization_alias")

                field_schema = field["schema"]

                if field_schema["type"] == "literal":
                    for entry in cast("LiteralSchema", field_schema)["expected"]:
                        if isinstance(entry, str):
                            mapping[entry] = variant
            else:
                field_info = cast("dict[str, FieldInfo]", variant.__fields__).get(discriminator_field_name)  # pyright: ignore[reportDeprecated, reportUnnecessaryCast]
                if not field_info:
                    continue

                # Note: if one variant defines an alias then they all should
                discriminator_alias = field_info.alias

                if (annotation := getattr(field_info, "annotation", None)) and is_literal_type(annotation):
                    for entry in get_args(annotation):
                        if isinstance(entry, str):
                            mapping[entry] = variant

    if not mapping:
        return None

    details = DiscriminatorDetails(
        mapping=mapping,
        discriminator_field=discriminator_field_name,
        discriminator_alias=discriminator_alias,
    )
    cast(CachedDiscriminatorType, union).__discriminator__ = details
    return details


def _extract_field_schema_pv2(model: type[BaseModel], field_name: str) -> ModelField | None:
    """
    Extracts the core schema for a specific field from a Pydantic v2 model.
    
    Parameters:
        model (type[BaseModel]): The Pydantic v2 model class.
        field_name (str): The name of the field to extract.
    
    Returns:
        ModelField | None: The schema for the specified field, or None if not found.
    """
    schema = model.__pydantic_core_schema__
    if schema["type"] == "definitions":
        schema = schema["schema"]

    if schema["type"] != "model":
        return None

    schema = cast("ModelSchema", schema)
    fields_schema = schema["schema"]
    if fields_schema["type"] != "model-fields":
        return None

    fields_schema = cast("ModelFieldsSchema", fields_schema)
    field = fields_schema["fields"].get(field_name)
    if not field:
        return None

    return cast("ModelField", field)  # pyright: ignore[reportUnnecessaryCast]


def validate_type(*, type_: type[_T], value: object) -> _T:
    """
    Strictly validates that a value matches the specified type.
    
    If the type is a subclass of Pydantic's BaseModel, uses Pydantic's parsing logic; otherwise, performs strict validation for non-model types.
    
    Parameters:
        type_ (type[_T]): The expected type to validate against.
        value (object): The value to validate.
    
    Returns:
        _T: The validated value, guaranteed to match the specified type.
    """
    if inspect.isclass(type_) and issubclass(type_, pydantic.BaseModel):
        return cast(_T, parse_obj(type_, value))

    return cast(_T, _validate_non_model_type(type_=type_, value=value))


def set_pydantic_config(typ: Any, config: pydantic.ConfigDict) -> None:
    """
    Attach a Pydantic configuration dictionary to a type for use with Pydantic v2.
    
    This function sets the `__pydantic_config__` attribute on the given type. It has no effect when using Pydantic v1.
    """
    setattr(typ, "__pydantic_config__", config)  # noqa: B010


# our use of subclassing here causes weirdness for type checkers,
# so we just pretend that we don't subclass
if TYPE_CHECKING:
    GenericModel = BaseModel
else:

    class GenericModel(BaseGenericModel, BaseModel):
        pass


if PYDANTIC_V2:
    from pydantic import TypeAdapter as _TypeAdapter

    _CachedTypeAdapter = cast("TypeAdapter[object]", lru_cache(maxsize=None)(_TypeAdapter))

    if TYPE_CHECKING:
        from pydantic import TypeAdapter
    else:
        TypeAdapter = _CachedTypeAdapter

    def _validate_non_model_type(*, type_: type[_T], value: object) -> _T:
        """
        Validate a non-BaseModel type using Pydantic's TypeAdapter.
        
        Returns:
            The validated value coerced to the specified type.
        """
        return TypeAdapter(type_).validate_python(value)

elif not TYPE_CHECKING:  # TODO: condition is weird

    class RootModel(GenericModel, Generic[_T]):
        """Used as a placeholder to easily convert runtime types to a Pydantic format
        to provide validation.

        For example:
        ```py
        validated = RootModel[int](__root__="5").__root__
        # validated: 5
        ```
        """

        __root__: _T

    def _validate_non_model_type(*, type_: type[_T], value: object) -> _T:
        """
        Validate a value against a non-BaseModel type using a dynamically created Pydantic model.
        
        Parameters:
            type_ (type[_T]): The target type to validate against.
            value (object): The value to validate.
        
        Returns:
            _T: The validated value, coerced to the specified type.
        """
        model = _create_pydantic_model(type_).validate(value)
        return cast(_T, model.__root__)

    def _create_pydantic_model(type_: _T) -> Type[RootModel[_T]]:
        """
        Create a Pydantic RootModel parametrized by the given type.
        
        Returns:
            A RootModel subclass with its `__root__` field set to the specified type.
        """
        return RootModel[type_]  # type: ignore


class FinalRequestOptionsInput(TypedDict, total=False):
    method: Required[str]
    url: Required[str]
    params: Query
    headers: Headers
    max_retries: int
    timeout: float | Timeout | None
    files: HttpxRequestFiles | None
    idempotency_key: str
    json_data: Body
    extra_json: AnyMapping
    follow_redirects: bool


@final
class FinalRequestOptions(pydantic.BaseModel):
    method: str
    url: str
    params: Query = {}
    headers: Union[Headers, NotGiven] = NotGiven()
    max_retries: Union[int, NotGiven] = NotGiven()
    timeout: Union[float, Timeout, None, NotGiven] = NotGiven()
    files: Union[HttpxRequestFiles, None] = None
    idempotency_key: Union[str, None] = None
    post_parser: Union[Callable[[Any], Any], NotGiven] = NotGiven()
    follow_redirects: Union[bool, None] = None

    # It should be noted that we cannot use `json` here as that would override
    # a BaseModel method in an incompatible fashion.
    json_data: Union[Body, None] = None
    extra_json: Union[AnyMapping, None] = None

    if PYDANTIC_V2:
        model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)
    else:

        class Config(pydantic.BaseConfig):  # pyright: ignore[reportDeprecated]
            arbitrary_types_allowed: bool = True

    def get_max_retries(self, max_retries: int) -> int:
        """
        Return the maximum number of retries, using the instance value if set, otherwise the provided default.
        
        Parameters:
            max_retries (int): The default number of retries to use if the instance value is not set.
        
        Returns:
            int: The resolved maximum number of retries.
        """
        if isinstance(self.max_retries, NotGiven):
            return max_retries
        return self.max_retries

    def _strip_raw_response_header(self) -> None:
        """
        Removes the raw response header from the headers dictionary if it is present.
        """
        if not is_given(self.headers):
            return

        if self.headers.get(RAW_RESPONSE_HEADER):
            self.headers = {**self.headers}
            self.headers.pop(RAW_RESPONSE_HEADER)

    # override the `construct` method so that we can run custom transformations.
    # this is necessary as we don't want to do any actual runtime type checking
    # (which means we can't use validators) but we do want to ensure that `NotGiven`
    # values are not present
    #
    # type ignore required because we're adding explicit types to `**values`
    @classmethod
    def construct(  # type: ignore
        cls,
        _fields_set: set[str] | None = None,
        **values: Unpack[FinalRequestOptionsInput],
    ) -> FinalRequestOptions:
        """
        Create a `FinalRequestOptions` instance without validation, stripping any `NotGiven` sentinel values from mapping fields.
        
        Parameters:
            _fields_set (set[str] | None): Optional set of field names to mark as explicitly set.
            **values: Field values for the model, with any mapping values cleaned of `NotGiven` sentinels.
        
        Returns:
            FinalRequestOptions: An instance of the model with cleaned field values.
        """
        kwargs: dict[str, Any] = {
            # we unconditionally call `strip_not_given` on any value
            # as it will just ignore any non-mapping types
            key: strip_not_given(value)
            for key, value in values.items()
        }
        if PYDANTIC_V2:
            return super().model_construct(_fields_set, **kwargs)
        return cast(FinalRequestOptions, super().construct(_fields_set, **kwargs))  # pyright: ignore[reportDeprecated]

    if not TYPE_CHECKING:
        # type checkers incorrectly complain about this assignment
        model_construct = construct
