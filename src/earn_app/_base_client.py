from __future__ import annotations

import sys
import json
import time
import uuid
import email
import asyncio
import inspect
import logging
import platform
import email.utils
from types import TracebackType
from random import random
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Type,
    Union,
    Generic,
    Mapping,
    TypeVar,
    Iterable,
    Iterator,
    Optional,
    Generator,
    AsyncIterator,
    cast,
    overload,
)
from typing_extensions import Literal, override, get_origin

import anyio
import httpx
import distro
import pydantic
from httpx import URL
from pydantic import PrivateAttr

from . import _exceptions
from ._qs import Querystring
from ._files import to_httpx_files, async_to_httpx_files
from ._types import (
    NOT_GIVEN,
    Body,
    Omit,
    Query,
    Headers,
    Timeout,
    NotGiven,
    ResponseT,
    AnyMapping,
    PostParser,
    RequestFiles,
    HttpxSendArgs,
    RequestOptions,
    HttpxRequestFiles,
    ModelBuilderProtocol,
)
from ._utils import is_dict, is_list, asyncify, is_given, lru_cache, is_mapping
from ._compat import PYDANTIC_V2, model_copy, model_dump
from ._models import GenericModel, FinalRequestOptions, validate_type, construct_type
from ._response import (
    APIResponse,
    BaseAPIResponse,
    AsyncAPIResponse,
    extract_response_type,
)
from ._constants import (
    DEFAULT_TIMEOUT,
    MAX_RETRY_DELAY,
    DEFAULT_MAX_RETRIES,
    INITIAL_RETRY_DELAY,
    RAW_RESPONSE_HEADER,
    OVERRIDE_CAST_TO_HEADER,
    DEFAULT_CONNECTION_LIMITS,
)
from ._streaming import Stream, SSEDecoder, AsyncStream, SSEBytesDecoder
from ._exceptions import (
    APIStatusError,
    APITimeoutError,
    APIConnectionError,
    APIResponseValidationError,
)

log: logging.Logger = logging.getLogger(__name__)

# TODO: make base page type vars covariant
SyncPageT = TypeVar("SyncPageT", bound="BaseSyncPage[Any]")
AsyncPageT = TypeVar("AsyncPageT", bound="BaseAsyncPage[Any]")


_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)

_StreamT = TypeVar("_StreamT", bound=Stream[Any])
_AsyncStreamT = TypeVar("_AsyncStreamT", bound=AsyncStream[Any])

if TYPE_CHECKING:
    from httpx._config import (
        DEFAULT_TIMEOUT_CONFIG,  # pyright: ignore[reportPrivateImportUsage]
    )

    HTTPX_DEFAULT_TIMEOUT = DEFAULT_TIMEOUT_CONFIG
else:
    try:
        from httpx._config import DEFAULT_TIMEOUT_CONFIG as HTTPX_DEFAULT_TIMEOUT
    except ImportError:
        # taken from https://github.com/encode/httpx/blob/3ba5fe0d7ac70222590e759c31442b1cab263791/httpx/_config.py#L366
        HTTPX_DEFAULT_TIMEOUT = Timeout(5.0)


class PageInfo:
    """Stores the necessary information to build the request to retrieve the next page.

    Either `url` or `params` must be set.
    """

    url: URL | NotGiven
    params: Query | NotGiven
    json: Body | NotGiven

    @overload
    def __init__(
        self,
        *,
        url: URL,
    ) -> None: """
        Initialize PageInfo with a URL for the next page request.
        
        Parameters:
            url (URL): The URL to use for fetching the next page.
        """
        ...

    @overload
    def __init__(
        self,
        *,
        params: Query,
    ) -> None: """
        Initialize PageInfo with query parameters for the next page request.
        
        Parameters:
            params (Query): Query parameters to use for the next page.
        """
        ...

    @overload
    def __init__(
        self,
        *,
        json: Body,
    ) -> None: """
        Initialize PageInfo with a JSON body for the next page request.
        
        Parameters:
            json (Body): The JSON body to use for the next page request.
        """
        ...

    def __init__(
        self,
        *,
        url: URL | NotGiven = NOT_GIVEN,
        json: Body | NotGiven = NOT_GIVEN,
        params: Query | NotGiven = NOT_GIVEN,
    ) -> None:
        """
        Initialize a PageInfo instance specifying how to request the next page in a paginated API.
        
        Exactly one of `url`, `params`, or `json` should be provided to indicate the next page's request details.
        
        Parameters:
            url (URL | NotGiven): The full URL for the next page request.
            json (Body | NotGiven): The JSON body to use for the next page request.
            params (Query | NotGiven): The query parameters for the next page request.
        """
        self.url = url
        self.json = json
        self.params = params

    @override
    def __repr__(self) -> str:
        """
        Return a string representation of the PageInfo instance, indicating which attribute (url, json, or params) is set.
        """
        if self.url:
            return f"{self.__class__.__name__}(url={self.url})"
        if self.json:
            return f"{self.__class__.__name__}(json={self.json})"
        return f"{self.__class__.__name__}(params={self.params})"


class BasePage(GenericModel, Generic[_T]):
    """
    Defines the core interface for pagination.

    Type Args:
        ModelT: The pydantic model that represents an item in the response.

    Methods:
        has_next_page(): Check if there is another page available
        next_page_info(): Get the necessary information to make a request for the next page
    """

    _options: FinalRequestOptions = PrivateAttr()
    _model: Type[_T] = PrivateAttr()

    def has_next_page(self) -> bool:
        """
        Return whether there is a next page available in the pagination sequence.
        
        Returns:
            bool: True if the current page contains items and next page information is available; otherwise, False.
        """
        items = self._get_page_items()
        if not items:
            return False
        return self.next_page_info() is not None

    def next_page_info(self) -> Optional[PageInfo]: """
Return information required to request the next page of results, or None if there is no next page.

Returns:
    PageInfo or None: Details for constructing the next page request, or None if no further pages are available.
"""
...

    def _get_page_items(self) -> Iterable[_T]:  # type: ignore[empty-body]
        """
        Return an iterable of items contained on the current page.
        
        This method must be implemented by subclasses to provide access to the items for the current page in a paginated response.
        """
        ...

    def _params_from_url(self, url: URL) -> httpx.QueryParams:
        # TODO: do we have to preprocess params here?
        """
        Merge the stored request parameters with the query parameters extracted from the given URL.
        
        Returns:
            httpx.QueryParams: Combined query parameters from the stored options and the provided URL.
        """
        return httpx.QueryParams(cast(Any, self._options.params)).merge(url.params)

    def _info_to_options(self, info: PageInfo) -> FinalRequestOptions:
        """
        Converts a PageInfo object into updated request options for fetching the next page.
        
        Merges pagination details from the provided PageInfo into a copy of the current request options, updating query parameters, URL, or JSON body as appropriate. Raises an error if the PageInfo is in an unexpected state or if non-mapping JSON data is encountered.
        
        Returns:
            FinalRequestOptions: The updated request options for the next page request.
        """
        options = model_copy(self._options)
        options._strip_raw_response_header()

        if not isinstance(info.params, NotGiven):
            options.params = {**options.params, **info.params}
            return options

        if not isinstance(info.url, NotGiven):
            params = self._params_from_url(info.url)
            url = info.url.copy_with(params=params)
            options.params = dict(url.params)
            options.url = str(url)
            return options

        if not isinstance(info.json, NotGiven):
            if not is_mapping(info.json):
                raise TypeError("Pagination is only supported with mappings")

            if not options.json_data:
                options.json_data = {**info.json}
            else:
                if not is_mapping(options.json_data):
                    raise TypeError("Pagination is only supported with mappings")

                options.json_data = {**options.json_data, **info.json}
            return options

        raise ValueError("Unexpected PageInfo state")


class BaseSyncPage(BasePage[_T], Generic[_T]):
    _client: SyncAPIClient = pydantic.PrivateAttr()

    def _set_private_attributes(
        self,
        client: SyncAPIClient,
        model: Type[_T],
        options: FinalRequestOptions,
    ) -> None:
        """
        Set the internal client, model, and request options for the page instance.
        
        This method also initializes the Pydantic private attributes dictionary if using Pydantic v2 and it is not already set.
        """
        if PYDANTIC_V2 and getattr(self, "__pydantic_private__", None) is None:
            self.__pydantic_private__ = {}

        self._model = model
        self._client = client
        self._options = options

    # Pydantic uses a custom `__iter__` method to support casting BaseModels
    # to dictionaries. e.g. dict(model).
    # As we want to support `for item in page`, this is inherently incompatible
    # with the default pydantic behaviour. It is not possible to support both
    # use cases at once. Fortunately, this is not a big deal as all other pydantic
    # methods should continue to work as expected as there is an alternative method
    # to cast a model to a dictionary, model.dict(), which is used internally
    # by pydantic.
    def __iter__(self) -> Iterator[_T]:  # type: ignore
        """
        Iterate over all items across paginated results.
        
        Yields:
            Each item from all pages in sequence.
        """
        for page in self.iter_pages():
            for item in page._get_page_items():
                yield item

    def iter_pages(self: SyncPageT) -> Iterator[SyncPageT]:
        """
        Iterates over all pages in a paginated API response.
        
        Yields:
            Each page object in sequence until no further pages are available.
        """
        page = self
        while True:
            yield page
            if page.has_next_page():
                page = page.get_next_page()
            else:
                return

    def get_next_page(self: SyncPageT) -> SyncPageT:
        """
        Retrieves the next page of results in a paginated API response.
        
        Returns:
            SyncPageT: The next page object.
        
        Raises:
            RuntimeError: If there is no next page available. Call `.has_next_page()` before invoking this method.
        """
        info = self.next_page_info()
        if not info:
            raise RuntimeError(
                "No next page expected; please check `.has_next_page()` before calling `.get_next_page()`."
            )

        options = self._info_to_options(info)
        return self._client._request_api_list(self._model, page=self.__class__, options=options)


class AsyncPaginator(Generic[_T, AsyncPageT]):
    def __init__(
        self,
        client: AsyncAPIClient,
        options: FinalRequestOptions,
        page_cls: Type[AsyncPageT],
        model: Type[_T],
    ) -> None:
        """
        Initialize the asynchronous paginator with the client, request options, page class, and item model type.
        
        Parameters:
            client (AsyncAPIClient): The asynchronous API client used to fetch pages.
            options (FinalRequestOptions): The request options for the initial page.
            page_cls (Type[AsyncPageT]): The class used to represent each page of results.
            model (Type[_T]): The type of items contained in each page.
        """
        self._model = model
        self._client = client
        self._options = options
        self._page_cls = page_cls

    def __await__(self) -> Generator[Any, None, AsyncPageT]:
        """
        Allows awaiting the paginator to retrieve the first page asynchronously.
        
        Returns:
            The first page of results as an instance of the asynchronous page type.
        """
        return self._get_page().__await__()

    async def _get_page(self) -> AsyncPageT:
        """
        Fetches a page of results asynchronously and injects client, model, and options into the page instance.
        
        Returns:
            AsyncPageT: The page object with private attributes set for further pagination.
        """
        def _parser(resp: AsyncPageT) -> AsyncPageT:
            resp._set_private_attributes(
                model=self._model,
                options=self._options,
                client=self._client,
            )
            return resp

        self._options.post_parser = _parser

        return await self._client.request(self._page_cls, self._options)

    async def __aiter__(self) -> AsyncIterator[_T]:
        # https://github.com/microsoft/pyright/issues/3464
        """
        Asynchronously iterates over all items across paginated API responses.
        
        Yields:
            Items of type `_T` from each page, iterating through all available pages asynchronously.
        """
        page = cast(
            AsyncPageT,
            await self,  # type: ignore
        )
        async for item in page:
            yield item


class BaseAsyncPage(BasePage[_T], Generic[_T]):
    _client: AsyncAPIClient = pydantic.PrivateAttr()

    def _set_private_attributes(
        self,
        model: Type[_T],
        client: AsyncAPIClient,
        options: FinalRequestOptions,
    ) -> None:
        """
        Set the internal model, client, and request options for the asynchronous page instance.
        
        This method is used to inject the expected item model type, the asynchronous API client, and the request options into the page object, typically after it is constructed.
        """
        if PYDANTIC_V2 and getattr(self, "__pydantic_private__", None) is None:
            self.__pydantic_private__ = {}

        self._model = model
        self._client = client
        self._options = options

    async def __aiter__(self) -> AsyncIterator[_T]:
        """
        Asynchronously iterates over all items across paginated API responses.
        
        Yields:
            Items of type `_T` from each page, one at a time, until all pages are exhausted.
        """
        async for page in self.iter_pages():
            for item in page._get_page_items():
                yield item

    async def iter_pages(self: AsyncPageT) -> AsyncIterator[AsyncPageT]:
        """
        Asynchronously iterates over all pages, yielding each page in sequence until no next page is available.
        
        Yields:
            AsyncPageT: The current page object for each iteration.
        """
        page = self
        while True:
            yield page
            if page.has_next_page():
                page = await page.get_next_page()
            else:
                return

    async def get_next_page(self: AsyncPageT) -> AsyncPageT:
        """
        Asynchronously retrieves the next page of results in a paginated API response.
        
        Returns:
            AsyncPageT: The next page object.
        
        Raises:
            RuntimeError: If there is no next page available. Check `.has_next_page()` before calling this method.
        """
        info = self.next_page_info()
        if not info:
            raise RuntimeError(
                "No next page expected; please check `.has_next_page()` before calling `.get_next_page()`."
            )

        options = self._info_to_options(info)
        return await self._client._request_api_list(self._model, page=self.__class__, options=options)


_HttpxClientT = TypeVar("_HttpxClientT", bound=Union[httpx.Client, httpx.AsyncClient])
_DefaultStreamT = TypeVar("_DefaultStreamT", bound=Union[Stream[Any], AsyncStream[Any]])


class BaseClient(Generic[_HttpxClientT, _DefaultStreamT]):
    _client: _HttpxClientT
    _version: str
    _base_url: URL
    max_retries: int
    timeout: Union[float, Timeout, None]
    _strict_response_validation: bool
    _idempotency_header: str | None
    _default_stream_cls: type[_DefaultStreamT] | None = None

    def __init__(
        self,
        *,
        version: str,
        base_url: str | URL,
        _strict_response_validation: bool,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float | Timeout | None = DEFAULT_TIMEOUT,
        custom_headers: Mapping[str, str] | None = None,
        custom_query: Mapping[str, object] | None = None,
    ) -> None:
        """
        Initialize the base HTTP client with configuration for versioning, base URL, retries, timeouts, and custom headers or query parameters.
        
        Raises:
            TypeError: If `max_retries` is set to None.
        """
        self._version = version
        self._base_url = self._enforce_trailing_slash(URL(base_url))
        self.max_retries = max_retries
        self.timeout = timeout
        self._custom_headers = custom_headers or {}
        self._custom_query = custom_query or {}
        self._strict_response_validation = _strict_response_validation
        self._idempotency_header = None
        self._platform: Platform | None = None

        if max_retries is None:  # pyright: ignore[reportUnnecessaryComparison]
            raise TypeError(
                "max_retries cannot be None. If you want to disable retries, pass `0`; if you want unlimited retries, pass `math.inf` or a very high number; if you want the default behavior, pass `earn_app.DEFAULT_MAX_RETRIES`"
            )

    def _enforce_trailing_slash(self, url: URL) -> URL:
        """
        Ensure that the given URL ends with a trailing slash.
        
        Returns:
            URL: The original URL if it already ends with a slash, otherwise a copy with a trailing slash appended.
        """
        if url.raw_path.endswith(b"/"):
            return url
        return url.copy_with(raw_path=url.raw_path + b"/")

    def _make_status_error_from_response(
        self,
        response: httpx.Response,
    ) -> APIStatusError:
        """
        Create an APIStatusError from an HTTP response, extracting error details from the response body if available.
        
        Attempts to parse the response body as JSON for detailed error information; falls back to plain text or status code if parsing fails.
        """
        if response.is_closed and not response.is_stream_consumed:
            # We can't read the response body as it has been closed
            # before it was read. This can happen if an event hook
            # raises a status error.
            body = None
            err_msg = f"Error code: {response.status_code}"
        else:
            err_text = response.text.strip()
            body = err_text

            try:
                body = json.loads(err_text)
                err_msg = f"Error code: {response.status_code} - {body}"
            except Exception:
                err_msg = err_text or f"Error code: {response.status_code}"

        return self._make_status_error(err_msg, body=body, response=response)

    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> _exceptions.APIStatusError:
        """
        Raises an APIStatusError for an HTTP response with an error.
        
        This method must be implemented by subclasses to construct and raise an APIStatusError using the provided error message, response body, and HTTP response.
        """
        raise NotImplementedError()

    def _build_headers(self, options: FinalRequestOptions, *, retries_taken: int = 0) -> httpx.Headers:
        """
        Construct and return HTTP headers for a request, merging defaults, custom headers, idempotency keys, and retry metadata.
        
        Parameters:
            options (FinalRequestOptions): The finalized request options containing custom headers, idempotency key, and timeout.
            retries_taken (int): The number of retry attempts made for this request.
        
        Returns:
            httpx.Headers: The complete set of headers to include with the HTTP request.
        """
        custom_headers = options.headers or {}
        headers_dict = _merge_mappings(self.default_headers, custom_headers)
        self._validate_headers(headers_dict, custom_headers)

        # headers are case-insensitive while dictionaries are not.
        headers = httpx.Headers(headers_dict)

        idempotency_header = self._idempotency_header
        if idempotency_header and options.idempotency_key and idempotency_header not in headers:
            headers[idempotency_header] = options.idempotency_key

        # Don't set these headers if they were already set or removed by the caller. We check
        # `custom_headers`, which can contain `Omit()`, instead of `headers` to account for the removal case.
        lower_custom_headers = [header.lower() for header in custom_headers]
        if "x-stainless-retry-count" not in lower_custom_headers:
            headers["x-stainless-retry-count"] = str(retries_taken)
        if "x-stainless-read-timeout" not in lower_custom_headers:
            timeout = self.timeout if isinstance(options.timeout, NotGiven) else options.timeout
            if isinstance(timeout, Timeout):
                timeout = timeout.read
            if timeout is not None:
                headers["x-stainless-read-timeout"] = str(timeout)

        return headers

    def _prepare_url(self, url: str) -> URL:
        """
        Combines the provided URL with the client's base URL if the input is relative, returning the absolute URL for the request.
        
        Parameters:
            url (str): The URL to merge, which may be relative or absolute.
        
        Returns:
            URL: The resulting absolute URL to be used for the outgoing request.
        """
        # Copied from httpx's `_merge_url` method.
        merge_url = URL(url)
        if merge_url.is_relative_url:
            merge_raw_path = self.base_url.raw_path + merge_url.raw_path.lstrip(b"/")
            return self.base_url.copy_with(raw_path=merge_raw_path)

        return merge_url

    def _make_sse_decoder(self) -> SSEDecoder | SSEBytesDecoder:
        """
        Return a new instance of the default server-sent events (SSE) decoder.
        """
        return SSEDecoder()

    def _build_request(
        self,
        options: FinalRequestOptions,
        *,
        retries_taken: int = 0,
    ) -> httpx.Request:
        """
        Constructs an `httpx.Request` object with merged headers, parameters, and body, handling multipart form data and custom content types.
        
        If the request is a multipart form submission, ensures proper encoding and boundary handling for compatibility with `httpx` and server requirements. Merges default and custom headers and parameters, serializes JSON or multipart data as needed, and applies any necessary workarounds for known HTTPX issues. Returns a fully prepared request ready to be sent by the HTTP client.
        
        Parameters:
            options (FinalRequestOptions): The finalized request options including method, URL, headers, parameters, body, files, and timeout.
            retries_taken (int, optional): The number of retry attempts already made for this request. Defaults to 0.
        
        Returns:
            httpx.Request: The constructed HTTP request object.
        """
        if log.isEnabledFor(logging.DEBUG):
            log.debug("Request options: %s", model_dump(options, exclude_unset=True))

        kwargs: dict[str, Any] = {}

        json_data = options.json_data
        if options.extra_json is not None:
            if json_data is None:
                json_data = cast(Body, options.extra_json)
            elif is_mapping(json_data):
                json_data = _merge_mappings(json_data, options.extra_json)
            else:
                raise RuntimeError(f"Unexpected JSON data type, {type(json_data)}, cannot merge with `extra_body`")

        headers = self._build_headers(options, retries_taken=retries_taken)
        params = _merge_mappings(self.default_query, options.params)
        content_type = headers.get("Content-Type")
        files = options.files

        # If the given Content-Type header is multipart/form-data then it
        # has to be removed so that httpx can generate the header with
        # additional information for us as it has to be in this form
        # for the server to be able to correctly parse the request:
        # multipart/form-data; boundary=---abc--
        if content_type is not None and content_type.startswith("multipart/form-data"):
            if "boundary" not in content_type:
                # only remove the header if the boundary hasn't been explicitly set
                # as the caller doesn't want httpx to come up with their own boundary
                headers.pop("Content-Type")

            # As we are now sending multipart/form-data instead of application/json
            # we need to tell httpx to use it, https://www.python-httpx.org/advanced/clients/#multipart-file-encoding
            if json_data:
                if not is_dict(json_data):
                    raise TypeError(
                        f"Expected query input to be a dictionary for multipart requests but got {type(json_data)} instead."
                    )
                kwargs["data"] = self._serialize_multipartform(json_data)

            # httpx determines whether or not to send a "multipart/form-data"
            # request based on the truthiness of the "files" argument.
            # This gets around that issue by generating a dict value that
            # evaluates to true.
            #
            # https://github.com/encode/httpx/discussions/2399#discussioncomment-3814186
            if not files:
                files = cast(HttpxRequestFiles, ForceMultipartDict())

        prepared_url = self._prepare_url(options.url)
        if "_" in prepared_url.host:
            # work around https://github.com/encode/httpx/discussions/2880
            kwargs["extensions"] = {"sni_hostname": prepared_url.host.replace("_", "-")}

        # TODO: report this error to httpx
        return self._client.build_request(  # pyright: ignore[reportUnknownMemberType]
            headers=headers,
            timeout=self.timeout if isinstance(options.timeout, NotGiven) else options.timeout,
            method=options.method,
            url=prepared_url,
            # the `Query` type that we use is incompatible with qs'
            # `Params` type as it needs to be typed as `Mapping[str, object]`
            # so that passing a `TypedDict` doesn't cause an error.
            # https://github.com/microsoft/pyright/issues/3526#event-6715453066
            params=self.qs.stringify(cast(Mapping[str, Any], params)) if params else None,
            json=json_data if is_given(json_data) else None,
            files=files,
            **kwargs,
        )

    def _serialize_multipartform(self, data: Mapping[object, object]) -> dict[str, object]:
        """
        Serialize a mapping into a dictionary suitable for multipart form data submission.
        
        Converts nested or repeated fields into a format compatible with HTTP multipart form encoding, ensuring that multiple values for the same key are represented as lists.
        """
        items = self.qs.stringify_items(
            # TODO: type ignore is required as stringify_items is well typed but we can't be
            # well typed without heavy validation.
            data,  # type: ignore
            array_format="brackets",
        )
        serialized: dict[str, object] = {}
        for key, value in items:
            existing = serialized.get(key)

            if not existing:
                serialized[key] = value
                continue

            # If a value has already been set for this key then that
            # means we're sending data like `array[]=[1, 2, 3]` and we
            # need to tell httpx that we want to send multiple values with
            # the same key which is done by using a list or a tuple.
            #
            # Note: 2d arrays should never result in the same key at both
            # levels so it's safe to assume that if the value is a list,
            # it was because we changed it to be a list.
            if is_list(existing):
                existing.append(value)
            else:
                serialized[key] = [existing, value]

        return serialized

    def _maybe_override_cast_to(self, cast_to: type[ResponseT], options: FinalRequestOptions) -> type[ResponseT]:
        """
        Checks for a temporary header to override the response type and updates headers accordingly.
        
        If the override header is present in the request options, returns the specified type and removes the header from the options; otherwise, returns the original type.
        """
        if not is_given(options.headers):
            return cast_to

        # make a copy of the headers so we don't mutate user-input
        headers = dict(options.headers)

        # we internally support defining a temporary header to override the
        # default `cast_to` type for use with `.with_raw_response` and `.with_streaming_response`
        # see _response.py for implementation details
        override_cast_to = headers.pop(OVERRIDE_CAST_TO_HEADER, NOT_GIVEN)
        if is_given(override_cast_to):
            options.headers = headers
            return cast(Type[ResponseT], override_cast_to)

        return cast_to

    def _should_stream_response_body(self, request: httpx.Request) -> bool:
        """
        Determine whether the response body for the given request should be streamed.
        
        Returns:
            bool: True if the request header indicates streaming is requested; otherwise, False.
        """
        return request.headers.get(RAW_RESPONSE_HEADER) == "stream"  # type: ignore[no-any-return]

    def _process_response_data(
        self,
        *,
        data: object,
        cast_to: type[ResponseT],
        response: httpx.Response,
    ) -> ResponseT:
        """
        Converts raw response data into the specified type, validating or constructing as needed.
        
        If the target type implements `ModelBuilderProtocol`, its `build` method is used. If strict response validation is enabled, the data is validated against the target type; otherwise, the type is constructed directly. Raises `APIResponseValidationError` if validation fails.
        
        Parameters:
            data (object): The parsed response data to process.
            cast_to (type[ResponseT]): The type to which the data should be converted.
            response (httpx.Response): The original HTTP response.
        
        Returns:
            ResponseT: The processed and validated response data.
        """
        if data is None:
            return cast(ResponseT, None)

        if cast_to is object:
            return cast(ResponseT, data)

        try:
            if inspect.isclass(cast_to) and issubclass(cast_to, ModelBuilderProtocol):
                return cast(ResponseT, cast_to.build(response=response, data=data))

            if self._strict_response_validation:
                return cast(ResponseT, validate_type(type_=cast_to, value=data))

            return cast(ResponseT, construct_type(type_=cast_to, value=data))
        except pydantic.ValidationError as err:
            raise APIResponseValidationError(response=response, body=data) from err

    @property
    def qs(self) -> Querystring:
        """
        Return a new instance of the query string helper.
        
        Returns:
        	Querystring: An object for building and manipulating URL query strings.
        """
        return Querystring()

    @property
    def custom_auth(self) -> httpx.Auth | None:
        """
        Returns the custom authentication handler for HTTP requests, or None if not set.
        """
        return None

    @property
    def auth_headers(self) -> dict[str, str]:
        """
        Return a dictionary of authentication headers to include in each request.
        
        Returns:
            dict[str, str]: Authentication headers as key-value pairs. Defaults to an empty dictionary.
        """
        return {}

    @property
    def default_headers(self) -> dict[str, str | Omit]:
        """
        Return the default HTTP headers for requests, including content type, user agent, platform, authentication, and any custom headers.
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            **self.platform_headers(),
            **self.auth_headers,
            **self._custom_headers,
        }

    @property
    def default_query(self) -> dict[str, object]:
        """
        Return the default query parameters for requests, including any custom query values set on the client.
        
        Returns:
            dict[str, object]: The default query parameters to include with each request.
        """
        return {
            **self._custom_query,
        }

    def _validate_headers(
        self,
        headers: Headers,  # noqa: ARG002
        custom_headers: Headers,  # noqa: ARG002
    ) -> None:
        """
        Validates the provided default and custom headers.
        
        This method is a no-op by default and can be overridden to implement custom header validation logic.
        """
        return

    @property
    def user_agent(self) -> str:
        """
        Return the default user agent string for the client, including the class name and package version.
        """
        return f"{self.__class__.__name__}/Python {self._version}"

    @property
    def base_url(self) -> URL:
        """
        Returns the current base URL used for all API requests.
        """
        return self._base_url

    @base_url.setter
    def base_url(self, url: URL | str) -> None:
        """
        Set the base URL for the client, ensuring it ends with a trailing slash.
        """
        self._base_url = self._enforce_trailing_slash(url if isinstance(url, URL) else URL(url))

    def platform_headers(self) -> Dict[str, str]:
        # the actual implementation is in a separate `lru_cache` decorated
        # function because adding `lru_cache` to methods will leak memory
        # https://github.com/python/cpython/issues/88476
        """
        Return HTTP headers containing platform and environment metadata for the client instance.
        
        Returns:
            Dict[str, str]: A dictionary of headers describing the client version, operating system, architecture, and Python runtime.
        """
        return platform_headers(self._version, platform=self._platform)

    def _parse_retry_after_header(self, response_headers: Optional[httpx.Headers] = None) -> float | None:
        """
        Parses the `Retry-After` or `retry-after-ms` headers to determine the number of seconds to wait before retrying a request.
        
        Returns:
            float | None: The number of seconds to wait, or None if no retry delay is specified.
        """
        if response_headers is None:
            return None

        # First, try the non-standard `retry-after-ms` header for milliseconds,
        # which is more precise than integer-seconds `retry-after`
        try:
            retry_ms_header = response_headers.get("retry-after-ms", None)
            return float(retry_ms_header) / 1000
        except (TypeError, ValueError):
            pass

        # Next, try parsing `retry-after` header as seconds (allowing nonstandard floats).
        retry_header = response_headers.get("retry-after")
        try:
            # note: the spec indicates that this should only ever be an integer
            # but if someone sends a float there's no reason for us to not respect it
            return float(retry_header)
        except (TypeError, ValueError):
            pass

        # Last, try parsing `retry-after` as a date.
        retry_date_tuple = email.utils.parsedate_tz(retry_header)
        if retry_date_tuple is None:
            return None

        retry_date = email.utils.mktime_tz(retry_date_tuple)
        return float(retry_date - time.time())

    def _calculate_retry_timeout(
        self,
        remaining_retries: int,
        options: FinalRequestOptions,
        response_headers: Optional[httpx.Headers] = None,
    ) -> float:
        """
        Calculate the delay before the next retry attempt using exponential backoff, optional server-suggested delay, and jitter.
        
        If the server provides a `Retry-After` header with a value between 0 and 60 seconds, that value is used. Otherwise, the delay is computed using exponential backoff based on the number of retries already taken, capped to avoid overflow, and includes random jitter to prevent thundering herd problems.
        
        Parameters:
            remaining_retries (int): The number of retries left for the request.
            options (FinalRequestOptions): The request options, used to determine the maximum allowed retries.
            response_headers (Optional[httpx.Headers]): HTTP response headers, used to check for server-suggested retry delay.
        
        Returns:
            float: The number of seconds to wait before the next retry attempt.
        """
        max_retries = options.get_max_retries(self.max_retries)

        # If the API asks us to wait a certain amount of time (and it's a reasonable amount), just do what it says.
        retry_after = self._parse_retry_after_header(response_headers)
        if retry_after is not None and 0 < retry_after <= 60:
            return retry_after

        # Also cap retry count to 1000 to avoid any potential overflows with `pow`
        nb_retries = min(max_retries - remaining_retries, 1000)

        # Apply exponential backoff, but not more than the max.
        sleep_seconds = min(INITIAL_RETRY_DELAY * pow(2.0, nb_retries), MAX_RETRY_DELAY)

        # Apply some jitter, plus-or-minus half a second.
        jitter = 1 - 0.25 * random()
        timeout = sleep_seconds * jitter
        return timeout if timeout >= 0 else 0

    def _should_retry(self, response: httpx.Response) -> bool:
        # Note: this is not a standard header
        """
        Determine whether a request should be retried based on the HTTP response.
        
        Returns True if the response indicates a retry is appropriate, such as when the server sets the `x-should-retry` header to "true", or for specific status codes (408, 409, 429, or any 5xx error). Returns False otherwise.
        """
        should_retry_header = response.headers.get("x-should-retry")

        # If the server explicitly says whether or not to retry, obey.
        if should_retry_header == "true":
            log.debug("Retrying as header `x-should-retry` is set to `true`")
            return True
        if should_retry_header == "false":
            log.debug("Not retrying as header `x-should-retry` is set to `false`")
            return False

        # Retry on request timeouts.
        if response.status_code == 408:
            log.debug("Retrying due to status code %i", response.status_code)
            return True

        # Retry on lock timeouts.
        if response.status_code == 409:
            log.debug("Retrying due to status code %i", response.status_code)
            return True

        # Retry on rate limits.
        if response.status_code == 429:
            log.debug("Retrying due to status code %i", response.status_code)
            return True

        # Retry internal errors.
        if response.status_code >= 500:
            log.debug("Retrying due to status code %i", response.status_code)
            return True

        log.debug("Not retrying")
        return False

    def _idempotency_key(self) -> str:
        """
        Generate a unique idempotency key for retryable HTTP requests.
        
        Returns:
            str: A unique idempotency key string.
        """
        return f"stainless-python-retry-{uuid.uuid4()}"


class _DefaultHttpxClient(httpx.Client):
    def __init__(self, **kwargs: Any) -> None:
        """
        Initializes the HTTP client with default timeout, connection limits, and redirect-following behavior unless overridden.
        """
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        kwargs.setdefault("limits", DEFAULT_CONNECTION_LIMITS)
        kwargs.setdefault("follow_redirects", True)
        super().__init__(**kwargs)


if TYPE_CHECKING:
    DefaultHttpxClient = httpx.Client
    """An alias to `httpx.Client` that provides the same defaults that this SDK
    uses internally.

    This is useful because overriding the `http_client` with your own instance of
    `httpx.Client` will result in httpx's defaults being used, not ours.
    """
else:
    DefaultHttpxClient = _DefaultHttpxClient


class SyncHttpxClientWrapper(DefaultHttpxClient):
    def __del__(self) -> None:
        """
        Ensures the client is closed when the object is deleted, suppressing any exceptions during closure.
        """
        if self.is_closed:
            return

        try:
            self.close()
        except Exception:
            pass


class SyncAPIClient(BaseClient[httpx.Client, Stream[Any]]):
    _client: httpx.Client
    _default_stream_cls: type[Stream[Any]] | None = None

    def __init__(
        self,
        *,
        version: str,
        base_url: str | URL,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
        http_client: httpx.Client | None = None,
        custom_headers: Mapping[str, str] | None = None,
        custom_query: Mapping[str, object] | None = None,
        _strict_response_validation: bool,
    ) -> None:
        """
        Initializes a synchronous API client with configurable HTTP client, base URL, retry policy, timeout, and custom headers or query parameters.
        
        Parameters:
            version (str): The package or API version string.
            base_url (str | URL): The base URL for all API requests.
            max_retries (int, optional): Maximum number of automatic retries for failed requests. Defaults to DEFAULT_MAX_RETRIES.
            timeout (float | Timeout | None | NotGiven, optional): Request timeout configuration. If not provided, uses the timeout from the provided HTTP client or a default value.
            http_client (httpx.Client, optional): Custom `httpx.Client` instance to use for HTTP requests. If not provided, a default client is created.
            custom_headers (Mapping[str, str], optional): Additional headers to include with every request.
            custom_query (Mapping[str, object], optional): Additional query parameters to include with every request.
            _strict_response_validation (bool): Whether to enforce strict response validation.
        """
        if not is_given(timeout):
            # if the user passed in a custom http client with a non-default
            # timeout set then we use that timeout.
            #
            # note: there is an edge case here where the user passes in a client
            # where they've explicitly set the timeout to match the default timeout
            # as this check is structural, meaning that we'll think they didn't
            # pass in a timeout and will ignore it
            if http_client and http_client.timeout != HTTPX_DEFAULT_TIMEOUT:
                timeout = http_client.timeout
            else:
                timeout = DEFAULT_TIMEOUT

        if http_client is not None and not isinstance(http_client, httpx.Client):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(
                f"Invalid `http_client` argument; Expected an instance of `httpx.Client` but got {type(http_client)}"
            )

        super().__init__(
            version=version,
            # cast to a valid type because mypy doesn't understand our type narrowing
            timeout=cast(Timeout, timeout),
            base_url=base_url,
            max_retries=max_retries,
            custom_query=custom_query,
            custom_headers=custom_headers,
            _strict_response_validation=_strict_response_validation,
        )
        self._client = http_client or SyncHttpxClientWrapper(
            base_url=base_url,
            # cast to a valid type because mypy doesn't understand our type narrowing
            timeout=cast(Timeout, timeout),
        )

    def is_closed(self) -> bool:
        """
        Return whether the underlying HTTP client is closed.
        """
        return self._client.is_closed

    def close(self) -> None:
        """
        Closes the underlying HTTPX client, rendering the client instance unusable for further requests.
        """
        # If an error is thrown while constructing a client, self._client
        # may not be present
        if hasattr(self, "_client"):
            self._client.close()

    def __enter__(self: _T) -> _T:
        """
        Enter the runtime context for the client, returning the client instance itself.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Closes the client when exiting a context manager block.
        """
        self.close()

    def _prepare_options(
        self,
        options: FinalRequestOptions,  # noqa: ARG002
    ) -> FinalRequestOptions:
        """
        Hook for modifying request options before sending a request.
        
        Parameters:
            options (FinalRequestOptions): The original request options to be potentially modified.
        
        Returns:
            FinalRequestOptions: The (possibly modified) request options.
        """
        return options

    def _prepare_request(
        self,
        request: httpx.Request,  # noqa: ARG002
    ) -> None:
        """
        Callback for mutating the constructed `httpx.Request` object before sending.
        
        Override this method to modify the request, such as adding headers based on request properties like URL or method.
        """
        return None

    @overload
    def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: Literal[True],
        stream_cls: Type[_StreamT],
    ) -> _StreamT: """
        Sends an HTTP request and returns a streaming response of the specified type.
        
        Parameters:
            cast_to (Type[ResponseT]): The expected response type for parsing the streamed data.
            options (FinalRequestOptions): The finalized request options including method, URL, headers, and body.
            stream (Literal[True]): Indicates that the response should be streamed.
            stream_cls (Type[_StreamT]): The stream class to use for handling the response.
        
        Returns:
            _StreamT: An instance of the specified stream class for consuming the streamed response.
        """
        ...

    @overload
    def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: Literal[False] = False,
    ) -> ResponseT: """
        Send an HTTP request and return the response parsed as the specified type.
        
        Parameters:
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            options (FinalRequestOptions): The finalized request options, including method, URL, headers, body, etc.
            stream (bool, optional): If True, returns a streaming response; otherwise, returns the parsed response. Defaults to False.
        
        Returns:
            ResponseT: The response parsed as the specified type, or a streaming response if requested.
        
        Raises:
            APIStatusError: If the response status code indicates an error.
            APITimeoutError: If the request times out.
            APIConnectionError: If a connection error occurs.
            APIResponseValidationError: If response validation fails when strict mode is enabled.
        """
        ...

    @overload
    def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: bool = False,
        stream_cls: Type[_StreamT] | None = None,
    ) -> ResponseT | _StreamT: """
        Send an HTTP request with the specified options and return the parsed response or a streaming response.
        
        Parameters:
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            options (FinalRequestOptions): The finalized request options including method, URL, headers, and body.
            stream (bool, optional): If True, returns a streaming response instead of parsing the body. Defaults to False.
            stream_cls (Type[_StreamT], optional): Custom stream class to use for streaming responses.
        
        Returns:
            ResponseT: The parsed response object of type `cast_to` if `stream` is False.
            _StreamT: An instance of the stream class if `stream` is True.
        
        Raises:
            APIStatusError: If the response status code indicates an error.
            APITimeoutError: If the request times out.
            APIConnectionError: If a connection error occurs.
            APIResponseValidationError: If response validation fails when strict mode is enabled.
        """
        ...

    def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: bool = False,
        stream_cls: type[_StreamT] | None = None,
    ) -> ResponseT | _StreamT:
        """
        Send an HTTP request with retry logic and process the response into the specified type.
        
        Attempts the request up to the configured maximum number of retries, handling timeouts, connection errors, and retryable HTTP status codes. If streaming is enabled, returns a stream object; otherwise, parses and validates the response into the provided type. Raises custom exceptions for timeouts, connection failures, or non-successful HTTP responses after all retries.
        
        Parameters:
            cast_to (Type[ResponseT]): The type to which the response should be parsed and validated.
            options (FinalRequestOptions): The finalized request options, including method, headers, body, and other settings.
            stream (bool, optional): If True, returns a streaming response. Defaults to False.
            stream_cls (type[_StreamT] | None, optional): Custom stream class to use for streaming responses.
        
        Returns:
            ResponseT | _StreamT: The parsed response object or a stream, depending on the `stream` parameter.
        """
        cast_to = self._maybe_override_cast_to(cast_to, options)

        # create a copy of the options we were given so that if the
        # options are mutated later & we then retry, the retries are
        # given the original options
        input_options = model_copy(options)
        if input_options.idempotency_key is None and input_options.method.lower() != "get":
            # ensure the idempotency key is reused between requests
            input_options.idempotency_key = self._idempotency_key()

        response: httpx.Response | None = None
        max_retries = input_options.get_max_retries(self.max_retries)

        retries_taken = 0
        for retries_taken in range(max_retries + 1):
            options = model_copy(input_options)
            options = self._prepare_options(options)

            remaining_retries = max_retries - retries_taken
            request = self._build_request(options, retries_taken=retries_taken)
            self._prepare_request(request)

            kwargs: HttpxSendArgs = {}
            if self.custom_auth is not None:
                kwargs["auth"] = self.custom_auth

            if options.follow_redirects is not None:
                kwargs["follow_redirects"] = options.follow_redirects

            log.debug("Sending HTTP Request: %s %s", request.method, request.url)

            response = None
            try:
                response = self._client.send(
                    request,
                    stream=stream or self._should_stream_response_body(request=request),
                    **kwargs,
                )
            except httpx.TimeoutException as err:
                log.debug("Encountered httpx.TimeoutException", exc_info=True)

                if remaining_retries > 0:
                    self._sleep_for_retry(
                        retries_taken=retries_taken,
                        max_retries=max_retries,
                        options=input_options,
                        response=None,
                    )
                    continue

                log.debug("Raising timeout error")
                raise APITimeoutError(request=request) from err
            except Exception as err:
                log.debug("Encountered Exception", exc_info=True)

                if remaining_retries > 0:
                    self._sleep_for_retry(
                        retries_taken=retries_taken,
                        max_retries=max_retries,
                        options=input_options,
                        response=None,
                    )
                    continue

                log.debug("Raising connection error")
                raise APIConnectionError(request=request) from err

            log.debug(
                'HTTP Response: %s %s "%i %s" %s',
                request.method,
                request.url,
                response.status_code,
                response.reason_phrase,
                response.headers,
            )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:  # thrown on 4xx and 5xx status code
                log.debug("Encountered httpx.HTTPStatusError", exc_info=True)

                if remaining_retries > 0 and self._should_retry(err.response):
                    err.response.close()
                    self._sleep_for_retry(
                        retries_taken=retries_taken,
                        max_retries=max_retries,
                        options=input_options,
                        response=response,
                    )
                    continue

                # If the response is streamed then we need to explicitly read the response
                # to completion before attempting to access the response text.
                if not err.response.is_closed:
                    err.response.read()

                log.debug("Re-raising status error")
                raise self._make_status_error_from_response(err.response) from None

            break

        assert response is not None, "could not resolve response (should never happen)"
        return self._process_response(
            cast_to=cast_to,
            options=options,
            response=response,
            stream=stream,
            stream_cls=stream_cls,
            retries_taken=retries_taken,
        )

    def _sleep_for_retry(
        self, *, retries_taken: int, max_retries: int, options: FinalRequestOptions, response: httpx.Response | None
    ) -> None:
        """
        Sleeps for a calculated duration before retrying an HTTP request.
        
        The sleep duration is determined based on the number of remaining retries, request options, and optional response headers, incorporating exponential backoff and server-suggested delays when available.
        """
        remaining_retries = max_retries - retries_taken
        if remaining_retries == 1:
            log.debug("1 retry left")
        else:
            log.debug("%i retries left", remaining_retries)

        timeout = self._calculate_retry_timeout(remaining_retries, options, response.headers if response else None)
        log.info("Retrying request to %s in %f seconds", options.url, timeout)

        time.sleep(timeout)

    def _process_response(
        self,
        *,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        response: httpx.Response,
        stream: bool,
        stream_cls: type[Stream[Any]] | type[AsyncStream[Any]] | None,
        retries_taken: int = 0,
    ) -> ResponseT:
        """
        Processes an HTTP response and returns it as the specified type, handling custom API response classes, streaming, and parsing.
        
        Parameters:
            cast_to (Type[ResponseT]): The expected return type, which may be a custom API response class or a model type.
            options (FinalRequestOptions): The finalized request options used for the request.
            response (httpx.Response): The HTTP response object to process.
            stream (bool): Whether the response should be streamed.
            stream_cls (type[Stream[Any]] | type[AsyncStream[Any]] | None): The stream class to use for streaming responses, if applicable.
            retries_taken (int, optional): The number of retries attempted for this request.
        
        Returns:
            ResponseT: The processed response, either as a raw HTTP response, a custom API response object, or a parsed model instance, depending on the parameters and response headers.
        
        Raises:
            TypeError: If a custom API response type does not subclass the expected base class.
        """
        origin = get_origin(cast_to) or cast_to

        if (
            inspect.isclass(origin)
            and issubclass(origin, BaseAPIResponse)
            # we only want to actually return the custom BaseAPIResponse class if we're
            # returning the raw response, or if we're not streaming SSE, as if we're streaming
            # SSE then `cast_to` doesn't actively reflect the type we need to parse into
            and (not stream or bool(response.request.headers.get(RAW_RESPONSE_HEADER)))
        ):
            if not issubclass(origin, APIResponse):
                raise TypeError(f"API Response types must subclass {APIResponse}; Received {origin}")

            response_cls = cast("type[BaseAPIResponse[Any]]", cast_to)
            return cast(
                ResponseT,
                response_cls(
                    raw=response,
                    client=self,
                    cast_to=extract_response_type(response_cls),
                    stream=stream,
                    stream_cls=stream_cls,
                    options=options,
                    retries_taken=retries_taken,
                ),
            )

        if cast_to == httpx.Response:
            return cast(ResponseT, response)

        api_response = APIResponse(
            raw=response,
            client=self,
            cast_to=cast("type[ResponseT]", cast_to),  # pyright: ignore[reportUnnecessaryCast]
            stream=stream,
            stream_cls=stream_cls,
            options=options,
            retries_taken=retries_taken,
        )
        if bool(response.request.headers.get(RAW_RESPONSE_HEADER)):
            return cast(ResponseT, api_response)

        return api_response.parse()

    def _request_api_list(
        self,
        model: Type[object],
        page: Type[SyncPageT],
        options: FinalRequestOptions,
    ) -> SyncPageT:
        """
        Requests a paginated API resource and injects client, model, and options into the resulting page object.
        
        Parameters:
            model (Type[object]): The Pydantic model class for items in the page.
            page (Type[SyncPageT]): The page class to parse the response into.
            options (FinalRequestOptions): The finalized request options for the API call.
        
        Returns:
            SyncPageT: An instance of the page class with private attributes set for pagination.
        """
        def _parser(resp: SyncPageT) -> SyncPageT:
            resp._set_private_attributes(
                client=self,
                model=model,
                options=options,
            )
            return resp

        options.post_parser = _parser

        return self.request(page, options, stream=False)

    @overload
    def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        options: RequestOptions = {},
        stream: Literal[False] = False,
    ) -> ResponseT: """
        Sends a synchronous HTTP GET request to the specified path and returns the response parsed as the given type.
        
        Parameters:
            path (str): The endpoint path to request, relative to the client's base URL.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
        
        Returns:
            ResponseT: The response parsed as the specified type.
        """
        ...

    @overload
    def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        options: RequestOptions = {},
        stream: Literal[True],
        stream_cls: type[_StreamT],
    ) -> _StreamT: """
        Sends a GET request to the specified path and returns a streaming response.
        
        Parameters:
            path (str): The endpoint path to send the GET request to.
            cast_to (Type[ResponseT]): The expected type for response parsing.
            options (RequestOptions, optional): Additional request options such as headers, query parameters, or timeout.
            stream (Literal[True]): Indicates that the response should be streamed.
            stream_cls (type[_StreamT]): The stream class to use for the response.
        
        Returns:
            _StreamT: An instance of the specified stream class for handling the streamed response.
        """
        ...

    @overload
    def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        options: RequestOptions = {},
        stream: bool,
        stream_cls: type[_StreamT] | None = None,
    ) -> ResponseT | _StreamT: """
        Send a synchronous HTTP GET request and return the response as the specified type or as a stream.
        
        Parameters:
            path (str): The relative or absolute URL path for the request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            options (RequestOptions, optional): Additional request options such as headers, query parameters, or body.
            stream (bool): If True, returns a streaming response using the specified stream class.
            stream_cls (type[_StreamT] | None, optional): Custom stream class to use if streaming is enabled.
        
        Returns:
            ResponseT or _StreamT: The parsed response object or a streaming response, depending on the value of `stream`.
        """
        ...

    def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        options: RequestOptions = {},
        stream: bool = False,
        stream_cls: type[_StreamT] | None = None,
    ) -> ResponseT | _StreamT:
        """
        Send a synchronous HTTP GET request and return the response as the specified type or as a stream.
        
        Parameters:
            path (str): The relative or absolute URL path for the GET request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            options (RequestOptions, optional): Additional request options such as headers, query parameters, or timeout.
            stream (bool, optional): If True, returns a streaming response using the specified stream class.
            stream_cls (type[_StreamT], optional): Custom stream class to use if streaming is enabled.
        
        Returns:
            ResponseT or _StreamT: The parsed response object of type `cast_to`, or a stream object if `stream` is True.
        """
        opts = FinalRequestOptions.construct(method="get", url=path, **options)
        # cast is required because mypy complains about returning Any even though
        # it understands the type variables
        return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))

    @overload
    def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        options: RequestOptions = {},
        files: RequestFiles | None = None,
        stream: Literal[False] = False,
    ) -> ResponseT: """
        Send a POST request to the specified path and return the response parsed as the given type.
        
        Parameters:
            path (str): The endpoint path to send the POST request to.
            cast_to (Type[ResponseT]): The type to parse the response into.
            body (Body | None): The request body to send, if any.
            options (RequestOptions): Additional request options such as headers, query parameters, or timeout.
            files (RequestFiles | None): Files to include in a multipart/form-data request.
            stream (Literal[False]): If False, returns the full parsed response.
        
        Returns:
            ResponseT: The response parsed as the specified type.
        """
        ...

    @overload
    def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        options: RequestOptions = {},
        files: RequestFiles | None = None,
        stream: Literal[True],
        stream_cls: type[_StreamT],
    ) -> _StreamT: """
        Send a POST request and return a streaming response of the specified type.
        
        Parameters:
            path (str): The endpoint path relative to the base URL.
            cast_to (Type[ResponseT]): The type to which the response should be cast.
            body (Body | None): The request body, if any.
            options (RequestOptions): Additional request options such as headers or query parameters.
            files (RequestFiles | None): Files to include in a multipart/form-data request.
            stream_cls (type[_StreamT]): The stream class to use for the response.
        
        Returns:
            _StreamT: An instance of the specified stream class for handling the streaming response.
        """
        ...

    @overload
    def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        options: RequestOptions = {},
        files: RequestFiles | None = None,
        stream: bool,
        stream_cls: type[_StreamT] | None = None,
    ) -> ResponseT | _StreamT: """
        Sends a POST request to the specified path and returns the response as the specified type or as a stream.
        
        Parameters:
            path (str): The endpoint path for the POST request.
            cast_to (Type[ResponseT]): The type to which the response should be cast.
            body (Body | None): The request body to send, if any.
            options (RequestOptions): Additional request options such as headers, query parameters, or timeout.
            files (RequestFiles | None): Files to include in a multipart/form-data request.
            stream (bool): Whether to return a streaming response.
            stream_cls (type[_StreamT] | None): Custom stream class to use if streaming.
        
        Returns:
            ResponseT | _StreamT: The parsed response object or a stream, depending on the `stream` parameter.
        """
        ...

    def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        options: RequestOptions = {},
        files: RequestFiles | None = None,
        stream: bool = False,
        stream_cls: type[_StreamT] | None = None,
    ) -> ResponseT | _StreamT:
        """
        Send a POST request to the specified path and return the response as the given type or as a stream.
        
        Parameters:
            path (str): The endpoint path or URL to send the POST request to.
            cast_to (Type[ResponseT]): The type to which the response should be cast.
            body (Body | None): The request body to send as JSON, if any.
            files (RequestFiles | None): Files to include in the request as multipart/form-data, if any.
            stream (bool): If True, returns a streaming response using the specified stream class.
            stream_cls (type[_StreamT] | None): Custom stream class to use for streaming responses.
        
        Returns:
            ResponseT | _StreamT: The parsed response object of type `cast_to`, or a stream if `stream` is True.
        """
        opts = FinalRequestOptions.construct(
            method="post", url=path, json_data=body, files=to_httpx_files(files), **options
        )
        return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))

    def patch(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        options: RequestOptions = {},
    ) -> ResponseT:
        """
        Send a PATCH request to the specified path and parse the response into the given type.
        
        Parameters:
            path (str): The endpoint path for the PATCH request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            body (Body | None): Optional JSON-serializable body to include in the request.
            options (RequestOptions): Optional request configuration.
        
        Returns:
            ResponseT: The parsed response object of the specified type.
        """
        opts = FinalRequestOptions.construct(method="patch", url=path, json_data=body, **options)
        return self.request(cast_to, opts)

    def put(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        files: RequestFiles | None = None,
        options: RequestOptions = {},
    ) -> ResponseT:
        """
        Send a PUT request to the specified path and parse the response into the given type.
        
        Parameters:
            path (str): The endpoint path or URL for the PUT request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            body (Body | None): Optional JSON-serializable request body.
            files (RequestFiles | None): Optional files to include as multipart form data.
            options (RequestOptions): Additional request options such as headers, query parameters, or timeout.
        
        Returns:
            ResponseT: The parsed response object of the specified type.
        """
        opts = FinalRequestOptions.construct(
            method="put", url=path, json_data=body, files=to_httpx_files(files), **options
        )
        return self.request(cast_to, opts)

    def delete(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        options: RequestOptions = {},
    ) -> ResponseT:
        """
        Send a DELETE request to the specified path and return the response parsed as the given type.
        
        Parameters:
            path (str): The endpoint path for the DELETE request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            body (Body | None): Optional JSON body to include in the request.
            options (RequestOptions): Additional request options.
        
        Returns:
            ResponseT: The parsed response object of the specified type.
        """
        opts = FinalRequestOptions.construct(method="delete", url=path, json_data=body, **options)
        return self.request(cast_to, opts)

    def get_api_list(
        self,
        path: str,
        *,
        model: Type[object],
        page: Type[SyncPageT],
        body: Body | None = None,
        options: RequestOptions = {},
        method: str = "get",
    ) -> SyncPageT:
        """
        Retrieve a paginated API resource and return the first page of results.
        
        Parameters:
            path (str): The API endpoint path.
            model (Type[object]): The data model class for items in the response.
            page (Type[SyncPageT]): The page class to use for pagination.
            body (Body | None, optional): The request body for methods like POST or PUT.
            options (RequestOptions, optional): Additional request options such as headers or query parameters.
            method (str, optional): The HTTP method to use (default is "get").
        
        Returns:
            SyncPageT: The first page of results as an instance of the specified page class.
        """
        opts = FinalRequestOptions.construct(method=method, url=path, json_data=body, **options)
        return self._request_api_list(model, page, opts)


class _DefaultAsyncHttpxClient(httpx.AsyncClient):
    def __init__(self, **kwargs: Any) -> None:
        """
        Initializes the HTTP client with default timeout, connection limits, and redirect-following behavior unless overridden.
        """
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        kwargs.setdefault("limits", DEFAULT_CONNECTION_LIMITS)
        kwargs.setdefault("follow_redirects", True)
        super().__init__(**kwargs)


try:
    import httpx_aiohttp
except ImportError:

    class _DefaultAioHttpClient(httpx.AsyncClient):
        def __init__(self, **_kwargs: Any) -> None:
            """
            Raises a RuntimeError indicating that the aiohttp client requires installation with the `aiohttp` extra.
            """
            raise RuntimeError("To use the aiohttp client you must have installed the package with the `aiohttp` extra")
else:

    class _DefaultAioHttpClient(httpx_aiohttp.HttpxAiohttpClient):  # type: ignore
        def __init__(self, **kwargs: Any) -> None:
            """
            Initializes the HTTP client with default timeout, connection limits, and redirect-following behavior unless overridden.
            """
            kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
            kwargs.setdefault("limits", DEFAULT_CONNECTION_LIMITS)
            kwargs.setdefault("follow_redirects", True)

            super().__init__(**kwargs)


if TYPE_CHECKING:
    DefaultAsyncHttpxClient = httpx.AsyncClient
    """An alias to `httpx.AsyncClient` that provides the same defaults that this SDK
    uses internally.

    This is useful because overriding the `http_client` with your own instance of
    `httpx.AsyncClient` will result in httpx's defaults being used, not ours.
    """

    DefaultAioHttpClient = httpx.AsyncClient
    """An alias to `httpx.AsyncClient` that changes the default HTTP transport to `aiohttp`."""
else:
    DefaultAsyncHttpxClient = _DefaultAsyncHttpxClient
    DefaultAioHttpClient = _DefaultAioHttpClient


class AsyncHttpxClientWrapper(DefaultAsyncHttpxClient):
    def __del__(self) -> None:
        """
        Ensures the asynchronous HTTP client is closed upon object deletion.
        
        If the client is not already closed, attempts to schedule its closure using the running event loop. Any exceptions during this process are silently ignored.
        """
        if self.is_closed:
            return

        try:
            # TODO(someday): support non asyncio runtimes here
            asyncio.get_running_loop().create_task(self.aclose())
        except Exception:
            pass


class AsyncAPIClient(BaseClient[httpx.AsyncClient, AsyncStream[Any]]):
    _client: httpx.AsyncClient
    _default_stream_cls: type[AsyncStream[Any]] | None = None

    def __init__(
        self,
        *,
        version: str,
        base_url: str | URL,
        _strict_response_validation: bool,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
        http_client: httpx.AsyncClient | None = None,
        custom_headers: Mapping[str, str] | None = None,
        custom_query: Mapping[str, object] | None = None,
    ) -> None:
        """
        Initialize an asynchronous API client with configurable base URL, version, retry policy, timeout, and optional custom HTTP client, headers, and query parameters.
        
        Raises:
            TypeError: If `http_client` is provided and is not an instance of `httpx.AsyncClient`.
        """
        if not is_given(timeout):
            # if the user passed in a custom http client with a non-default
            # timeout set then we use that timeout.
            #
            # note: there is an edge case here where the user passes in a client
            # where they've explicitly set the timeout to match the default timeout
            # as this check is structural, meaning that we'll think they didn't
            # pass in a timeout and will ignore it
            if http_client and http_client.timeout != HTTPX_DEFAULT_TIMEOUT:
                timeout = http_client.timeout
            else:
                timeout = DEFAULT_TIMEOUT

        if http_client is not None and not isinstance(http_client, httpx.AsyncClient):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(
                f"Invalid `http_client` argument; Expected an instance of `httpx.AsyncClient` but got {type(http_client)}"
            )

        super().__init__(
            version=version,
            base_url=base_url,
            # cast to a valid type because mypy doesn't understand our type narrowing
            timeout=cast(Timeout, timeout),
            max_retries=max_retries,
            custom_query=custom_query,
            custom_headers=custom_headers,
            _strict_response_validation=_strict_response_validation,
        )
        self._client = http_client or AsyncHttpxClientWrapper(
            base_url=base_url,
            # cast to a valid type because mypy doesn't understand our type narrowing
            timeout=cast(Timeout, timeout),
        )

    def is_closed(self) -> bool:
        """
        Return whether the underlying HTTP client is closed.
        """
        return self._client.is_closed

    async def close(self) -> None:
        """
        Asynchronously closes the underlying HTTPX client.
        
        After calling this method, the client instance cannot be used for further requests.
        """
        await self._client.aclose()

    async def __aenter__(self: _T) -> _T:
        """
        Enter the asynchronous context manager for this client.
        
        Returns:
            The client instance itself for use within an async with block.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Asynchronously exits the context manager, ensuring the underlying HTTP client is closed.
        """
        await self.close()

    async def _prepare_options(
        self,
        options: FinalRequestOptions,  # noqa: ARG002
    ) -> FinalRequestOptions:
        """
        Asynchronous hook for modifying request options before sending a request.
        
        Parameters:
            options (FinalRequestOptions): The original request options.
        
        Returns:
            FinalRequestOptions: The potentially modified request options.
        """
        return options

    async def _prepare_request(
        self,
        request: httpx.Request,  # noqa: ARG002
    ) -> None:
        """
        Callback for mutating the constructed `httpx.Request` object before sending.
        
        Override this method to modify the request, such as adding headers based on request properties like URL or method.
        """
        return None

    @overload
    async def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: Literal[False] = False,
    ) -> ResponseT: """
        Sends an asynchronous HTTP request and returns the response parsed as the specified type.
        
        Parameters:
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            options (FinalRequestOptions): The finalized request options, including URL, headers, parameters, and body.
            stream (bool, optional): If True, returns a streaming response; otherwise, returns the parsed response object. Defaults to False.
        
        Returns:
            ResponseT: The response parsed as the specified type, or a streaming response if `stream` is True.
        
        Raises:
            APIStatusError: If the response status code indicates an error.
            APITimeoutError: If the request times out.
            APIConnectionError: If a connection error occurs.
            APIResponseValidationError: If response validation fails and strict validation is enabled.
        """
        ...

    @overload
    async def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: Literal[True],
        stream_cls: type[_AsyncStreamT],
    ) -> _AsyncStreamT: """
        Send an asynchronous HTTP request and return a streaming response.
        
        Parameters:
            cast_to (Type[ResponseT]): The expected response type for parsing.
            options (FinalRequestOptions): The finalized request options.
            stream (Literal[True]): Indicates that the response should be streamed.
            stream_cls (type[_AsyncStreamT]): The stream class to use for the response.
        
        Returns:
            _AsyncStreamT: An asynchronous stream object for consuming the response body.
        """
        ...

    @overload
    async def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: bool,
        stream_cls: type[_AsyncStreamT] | None = None,
    ) -> ResponseT | _AsyncStreamT: """
        Sends an asynchronous HTTP request and returns the parsed response or a streaming response.
        
        Parameters:
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            options (FinalRequestOptions): The finalized request options including method, URL, headers, and body.
            stream (bool): If True, returns a streaming response; otherwise, returns the parsed response.
            stream_cls (type[_AsyncStreamT] | None): Optional custom stream class to use for streaming responses.
        
        Returns:
            ResponseT | _AsyncStreamT: The parsed response object or a streaming response, depending on the `stream` flag.
        """
        ...

    async def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: bool = False,
        stream_cls: type[_AsyncStreamT] | None = None,
    ) -> ResponseT | _AsyncStreamT:
        """
        Sends an asynchronous HTTP request with retry logic and processes the response.
        
        Parameters:
            cast_to (Type[ResponseT]): The expected type to cast the response to.
            options (FinalRequestOptions): The finalized request options.
            stream (bool, optional): Whether to stream the response body. Defaults to False.
            stream_cls (type[_AsyncStreamT] | None, optional): Custom stream class for streaming responses.
        
        Returns:
            ResponseT | _AsyncStreamT: The processed response, either as the specified type or as a stream if streaming is enabled.
        
        Raises:
            APITimeoutError: If the request times out and all retries are exhausted.
            APIConnectionError: If a connection error occurs and all retries are exhausted.
            APIStatusError: If a non-retryable HTTP error status is returned.
        """
        if self._platform is None:
            # `get_platform` can make blocking IO calls so we
            # execute it earlier while we are in an async context
            self._platform = await asyncify(get_platform)()

        cast_to = self._maybe_override_cast_to(cast_to, options)

        # create a copy of the options we were given so that if the
        # options are mutated later & we then retry, the retries are
        # given the original options
        input_options = model_copy(options)
        if input_options.idempotency_key is None and input_options.method.lower() != "get":
            # ensure the idempotency key is reused between requests
            input_options.idempotency_key = self._idempotency_key()

        response: httpx.Response | None = None
        max_retries = input_options.get_max_retries(self.max_retries)

        retries_taken = 0
        for retries_taken in range(max_retries + 1):
            options = model_copy(input_options)
            options = await self._prepare_options(options)

            remaining_retries = max_retries - retries_taken
            request = self._build_request(options, retries_taken=retries_taken)
            await self._prepare_request(request)

            kwargs: HttpxSendArgs = {}
            if self.custom_auth is not None:
                kwargs["auth"] = self.custom_auth

            if options.follow_redirects is not None:
                kwargs["follow_redirects"] = options.follow_redirects

            log.debug("Sending HTTP Request: %s %s", request.method, request.url)

            response = None
            try:
                response = await self._client.send(
                    request,
                    stream=stream or self._should_stream_response_body(request=request),
                    **kwargs,
                )
            except httpx.TimeoutException as err:
                log.debug("Encountered httpx.TimeoutException", exc_info=True)

                if remaining_retries > 0:
                    await self._sleep_for_retry(
                        retries_taken=retries_taken,
                        max_retries=max_retries,
                        options=input_options,
                        response=None,
                    )
                    continue

                log.debug("Raising timeout error")
                raise APITimeoutError(request=request) from err
            except Exception as err:
                log.debug("Encountered Exception", exc_info=True)

                if remaining_retries > 0:
                    await self._sleep_for_retry(
                        retries_taken=retries_taken,
                        max_retries=max_retries,
                        options=input_options,
                        response=None,
                    )
                    continue

                log.debug("Raising connection error")
                raise APIConnectionError(request=request) from err

            log.debug(
                'HTTP Response: %s %s "%i %s" %s',
                request.method,
                request.url,
                response.status_code,
                response.reason_phrase,
                response.headers,
            )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:  # thrown on 4xx and 5xx status code
                log.debug("Encountered httpx.HTTPStatusError", exc_info=True)

                if remaining_retries > 0 and self._should_retry(err.response):
                    await err.response.aclose()
                    await self._sleep_for_retry(
                        retries_taken=retries_taken,
                        max_retries=max_retries,
                        options=input_options,
                        response=response,
                    )
                    continue

                # If the response is streamed then we need to explicitly read the response
                # to completion before attempting to access the response text.
                if not err.response.is_closed:
                    await err.response.aread()

                log.debug("Re-raising status error")
                raise self._make_status_error_from_response(err.response) from None

            break

        assert response is not None, "could not resolve response (should never happen)"
        return await self._process_response(
            cast_to=cast_to,
            options=options,
            response=response,
            stream=stream,
            stream_cls=stream_cls,
            retries_taken=retries_taken,
        )

    async def _sleep_for_retry(
        self, *, retries_taken: int, max_retries: int, options: FinalRequestOptions, response: httpx.Response | None
    ) -> None:
        """
        Asynchronously waits for a calculated delay before retrying a failed HTTP request.
        
        The delay duration is determined based on the number of remaining retries, request options, and optional response headers, including support for server-suggested retry intervals.
        """
        remaining_retries = max_retries - retries_taken
        if remaining_retries == 1:
            log.debug("1 retry left")
        else:
            log.debug("%i retries left", remaining_retries)

        timeout = self._calculate_retry_timeout(remaining_retries, options, response.headers if response else None)
        log.info("Retrying request to %s in %f seconds", options.url, timeout)

        await anyio.sleep(timeout)

    async def _process_response(
        self,
        *,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        response: httpx.Response,
        stream: bool,
        stream_cls: type[Stream[Any]] | type[AsyncStream[Any]] | None,
        retries_taken: int = 0,
    ) -> ResponseT:
        """
        Processes an HTTP response and returns it as the specified type, handling custom API response classes and streaming.
        
        Parameters:
        	cast_to (Type[ResponseT]): The target type to cast the response to.
        
        Returns:
        	ResponseT: The processed response, either as a raw HTTPX response, a custom API response class, or a parsed model instance.
        
        Raises:
        	TypeError: If a custom API response class does not subclass AsyncAPIResponse.
        """
        origin = get_origin(cast_to) or cast_to

        if (
            inspect.isclass(origin)
            and issubclass(origin, BaseAPIResponse)
            # we only want to actually return the custom BaseAPIResponse class if we're
            # returning the raw response, or if we're not streaming SSE, as if we're streaming
            # SSE then `cast_to` doesn't actively reflect the type we need to parse into
            and (not stream or bool(response.request.headers.get(RAW_RESPONSE_HEADER)))
        ):
            if not issubclass(origin, AsyncAPIResponse):
                raise TypeError(f"API Response types must subclass {AsyncAPIResponse}; Received {origin}")

            response_cls = cast("type[BaseAPIResponse[Any]]", cast_to)
            return cast(
                "ResponseT",
                response_cls(
                    raw=response,
                    client=self,
                    cast_to=extract_response_type(response_cls),
                    stream=stream,
                    stream_cls=stream_cls,
                    options=options,
                    retries_taken=retries_taken,
                ),
            )

        if cast_to == httpx.Response:
            return cast(ResponseT, response)

        api_response = AsyncAPIResponse(
            raw=response,
            client=self,
            cast_to=cast("type[ResponseT]", cast_to),  # pyright: ignore[reportUnnecessaryCast]
            stream=stream,
            stream_cls=stream_cls,
            options=options,
            retries_taken=retries_taken,
        )
        if bool(response.request.headers.get(RAW_RESPONSE_HEADER)):
            return cast(ResponseT, api_response)

        return await api_response.parse()

    def _request_api_list(
        self,
        model: Type[_T],
        page: Type[AsyncPageT],
        options: FinalRequestOptions,
    ) -> AsyncPaginator[_T, AsyncPageT]:
        """
        Return an asynchronous paginator for iterating over a paginated API resource.
        
        Parameters:
            model: The Pydantic model type representing items in the paginated response.
            page: The page class implementing asynchronous pagination logic.
            options: The finalized request options for the API call.
        
        Returns:
            An AsyncPaginator instance for asynchronous iteration over paginated results.
        """
        return AsyncPaginator(client=self, options=options, page_cls=page, model=model)

    @overload
    async def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        options: RequestOptions = {},
        stream: Literal[False] = False,
    ) -> ResponseT: """
        Sends an asynchronous HTTP GET request to the specified path and returns the response parsed as the given type.
        
        Parameters:
            path (str): The relative or absolute URL path for the GET request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            options (RequestOptions, optional): Additional request options such as headers, query parameters, or timeout.
            stream (Literal[False], optional): If False, the response body is fully read and parsed (streaming is not supported for GET in this overload).
        
        Returns:
            ResponseT: The parsed response object of the specified type.
        """
        ...

    @overload
    async def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        options: RequestOptions = {},
        stream: Literal[True],
        stream_cls: type[_AsyncStreamT],
    ) -> _AsyncStreamT: """
        Sends an asynchronous HTTP GET request and returns a streaming response.
        
        Parameters:
            path (str): The URL path for the GET request.
            cast_to (Type[ResponseT]): The expected response type for parsing.
            options (RequestOptions, optional): Additional request options such as headers, query parameters, or timeout.
            stream (Literal[True]): Indicates that the response should be streamed.
            stream_cls (type[_AsyncStreamT]): The class to use for streaming the response.
        
        Returns:
            _AsyncStreamT: An instance of the specified stream class for handling the streamed response.
        """
        ...

    @overload
    async def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        options: RequestOptions = {},
        stream: bool,
        stream_cls: type[_AsyncStreamT] | None = None,
    ) -> ResponseT | _AsyncStreamT: """
        Sends an asynchronous HTTP GET request to the specified path and returns the parsed response or a streaming response.
        
        Parameters:
            path (str): The relative or absolute URL path for the GET request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            options (RequestOptions, optional): Additional request options such as headers, query parameters, or timeout.
            stream (bool): If True, returns a streaming response using the specified stream class.
            stream_cls (type[_AsyncStreamT] | None, optional): Custom stream class to use for streaming responses.
        
        Returns:
            ResponseT | _AsyncStreamT: The parsed response object of type `cast_to`, or a streaming response if `stream` is True.
        """
        ...

    async def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        options: RequestOptions = {},
        stream: bool = False,
        stream_cls: type[_AsyncStreamT] | None = None,
    ) -> ResponseT | _AsyncStreamT:
        """
        Sends an asynchronous HTTP GET request to the specified path and returns the parsed response or a streaming response.
        
        Parameters:
            path (str): The endpoint path or URL to send the GET request to.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            options (RequestOptions, optional): Additional request options such as headers, query parameters, or timeout.
            stream (bool, optional): If True, returns a streaming response instead of parsing the body.
            stream_cls (type[_AsyncStreamT], optional): Custom stream class to use for streaming responses.
        
        Returns:
            ResponseT | _AsyncStreamT: The parsed response object or a streaming response, depending on the `stream` flag.
        """
        opts = FinalRequestOptions.construct(method="get", url=path, **options)
        return await self.request(cast_to, opts, stream=stream, stream_cls=stream_cls)

    @overload
    async def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        files: RequestFiles | None = None,
        options: RequestOptions = {},
        stream: Literal[False] = False,
    ) -> ResponseT: """
        Send an asynchronous HTTP POST request to the specified path and return the response parsed as the given type.
        
        Parameters:
            path (str): The endpoint path to send the POST request to.
            cast_to (Type[ResponseT]): The type to parse the response into.
            body (Body | None): The request body to send, if any.
            files (RequestFiles | None): Files to include in the request, if any.
            options (RequestOptions): Additional request options such as headers, query parameters, or timeout.
            stream (Literal[False]): If False, returns the full parsed response.
        
        Returns:
            ResponseT: The response parsed as the specified type.
        """
        ...

    @overload
    async def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        files: RequestFiles | None = None,
        options: RequestOptions = {},
        stream: Literal[True],
        stream_cls: type[_AsyncStreamT],
    ) -> _AsyncStreamT: """
        Send an asynchronous HTTP POST request and return a streaming response.
        
        Parameters:
            path (str): The endpoint path to send the request to.
            cast_to (Type[ResponseT]): The expected response type for parsing.
            body (Body | None): The request body to send, if any.
            files (RequestFiles | None): Files to include in a multipart/form-data request.
            options (RequestOptions): Additional request options such as headers or query parameters.
            stream (Literal[True]): Indicates that the response should be streamed.
            stream_cls (type[_AsyncStreamT]): The stream class to use for the response.
        
        Returns:
            _AsyncStreamT: An asynchronous stream object for reading the response body.
        """
        ...

    @overload
    async def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        files: RequestFiles | None = None,
        options: RequestOptions = {},
        stream: bool,
        stream_cls: type[_AsyncStreamT] | None = None,
    ) -> ResponseT | _AsyncStreamT: """
        Send an asynchronous HTTP POST request to the specified path.
        
        Parameters:
            path (str): The endpoint path for the POST request.
            cast_to (Type[ResponseT]): The type to which the response should be cast.
            body (Body | None): The request body to send, if any.
            files (RequestFiles | None): Files to include in the request, if any.
            options (RequestOptions): Additional request options such as headers, query parameters, or timeout.
            stream (bool): Whether to stream the response.
            stream_cls (type[_AsyncStreamT] | None): Custom stream class to use if streaming.
        
        Returns:
            ResponseT | _AsyncStreamT: The parsed response object or a stream if streaming is enabled.
        """
        ...

    async def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        files: RequestFiles | None = None,
        options: RequestOptions = {},
        stream: bool = False,
        stream_cls: type[_AsyncStreamT] | None = None,
    ) -> ResponseT | _AsyncStreamT:
        """
        Sends an asynchronous HTTP POST request to the specified path.
        
        Parameters:
            path (str): The endpoint path or URL to send the POST request to.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            body (Body | None): Optional JSON-serializable request body.
            files (RequestFiles | None): Optional files to include in the request as multipart form data.
            options (RequestOptions): Additional request options such as headers, query parameters, or timeout.
            stream (bool): If True, returns a streaming response using the specified stream class.
            stream_cls (type[_AsyncStreamT] | None): Custom stream class to use for streaming responses.
        
        Returns:
            ResponseT | _AsyncStreamT: The parsed response object or a streaming response, depending on the `stream` flag.
        """
        opts = FinalRequestOptions.construct(
            method="post", url=path, json_data=body, files=await async_to_httpx_files(files), **options
        )
        return await self.request(cast_to, opts, stream=stream, stream_cls=stream_cls)

    async def patch(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        options: RequestOptions = {},
    ) -> ResponseT:
        """
        Send an asynchronous HTTP PATCH request to the specified path and return the response parsed as the given type.
        
        Parameters:
            path (str): The endpoint path for the PATCH request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            body (Body | None): Optional JSON-serializable body to include in the request.
            options (RequestOptions): Optional additional request options.
        
        Returns:
            ResponseT: The response parsed as the specified type.
        """
        opts = FinalRequestOptions.construct(method="patch", url=path, json_data=body, **options)
        return await self.request(cast_to, opts)

    async def put(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        files: RequestFiles | None = None,
        options: RequestOptions = {},
    ) -> ResponseT:
        """
        Send an asynchronous HTTP PUT request to the specified path and return the response parsed as the given type.
        
        Parameters:
            path (str): The endpoint path or URL for the PUT request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            body (Body | None): Optional JSON-serializable request body.
            files (RequestFiles | None): Optional files to include in the request.
            options (RequestOptions): Additional request options such as headers, query parameters, or timeout.
        
        Returns:
            ResponseT: The response parsed as the specified type.
        """
        opts = FinalRequestOptions.construct(
            method="put", url=path, json_data=body, files=await async_to_httpx_files(files), **options
        )
        return await self.request(cast_to, opts)

    async def delete(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT],
        body: Body | None = None,
        options: RequestOptions = {},
    ) -> ResponseT:
        """
        Sends an asynchronous HTTP DELETE request to the specified path and returns the response parsed as the given type.
        
        Parameters:
            path (str): The endpoint path for the DELETE request.
            cast_to (Type[ResponseT]): The type to which the response should be parsed.
            body (Body | None): Optional JSON body to include in the request.
            options (RequestOptions): Additional request options.
        
        Returns:
            ResponseT: The parsed response of the specified type.
        """
        opts = FinalRequestOptions.construct(method="delete", url=path, json_data=body, **options)
        return await self.request(cast_to, opts)

    def get_api_list(
        self,
        path: str,
        *,
        model: Type[_T],
        page: Type[AsyncPageT],
        body: Body | None = None,
        options: RequestOptions = {},
        method: str = "get",
    ) -> AsyncPaginator[_T, AsyncPageT]:
        """
        Returns an asynchronous paginator for iterating over a paginated API resource.
        
        Parameters:
            path (str): The API endpoint path.
            model (Type[_T]): The Pydantic model type for items in the paginated response.
            page (Type[AsyncPageT]): The page class used to represent each page of results.
            body (Body | None, optional): The request body for methods that support it.
            options (RequestOptions, optional): Additional request options such as headers, query parameters, or timeout.
            method (str, optional): The HTTP method to use (default is "get").
        
        Returns:
            AsyncPaginator[_T, AsyncPageT]: An asynchronous paginator yielding items of type `_T` from each page.
        """
        opts = FinalRequestOptions.construct(method=method, url=path, json_data=body, **options)
        return self._request_api_list(model, page, opts)


def make_request_options(
    *,
    query: Query | None = None,
    extra_headers: Headers | None = None,
    extra_query: Query | None = None,
    extra_body: Body | None = None,
    idempotency_key: str | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    post_parser: PostParser | NotGiven = NOT_GIVEN,
) -> RequestOptions:
    """
    Construct a RequestOptions dictionary by combining provided query parameters, headers, body, idempotency key, timeout, and post-parser, omitting any keys with NotGiven values.
    
    Parameters:
        query (dict, optional): Query parameters to include in the request.
        extra_headers (dict, optional): Additional headers to include.
        extra_query (dict, optional): Additional query parameters to merge with `query`.
        extra_body (dict, optional): Additional JSON body to include.
        idempotency_key (str, optional): Idempotency key for the request.
        timeout (float or httpx.Timeout or None, optional): Timeout setting for the request.
        post_parser (callable, optional): Optional post-processing function for the response.
    
    Returns:
        RequestOptions: A dictionary containing the merged request options, excluding any keys with NotGiven values.
    """
    options: RequestOptions = {}
    if extra_headers is not None:
        options["headers"] = extra_headers

    if extra_body is not None:
        options["extra_json"] = cast(AnyMapping, extra_body)

    if query is not None:
        options["params"] = query

    if extra_query is not None:
        options["params"] = {**options.get("params", {}), **extra_query}

    if not isinstance(timeout, NotGiven):
        options["timeout"] = timeout

    if idempotency_key is not None:
        options["idempotency_key"] = idempotency_key

    if is_given(post_parser):
        # internal
        options["post_parser"] = post_parser  # type: ignore

    return options


class ForceMultipartDict(Dict[str, None]):
    def __bool__(self) -> bool:
        """
        Always returns True, making the dictionary instance evaluate as truthy even if empty.
        """
        return True


class OtherPlatform:
    def __init__(self, name: str) -> None:
        """
        Initialize the object with the given name.
        
        Parameters:
            name (str): The name to associate with this instance.
        """
        self.name = name

    @override
    def __str__(self) -> str:
        """
        Return a string representation of the object in the format 'Other:{name}'.
        """
        return f"Other:{self.name}"


Platform = Union[
    OtherPlatform,
    Literal[
        "MacOS",
        "Linux",
        "Windows",
        "FreeBSD",
        "OpenBSD",
        "iOS",
        "Android",
        "Unknown",
    ],
]


def get_platform() -> Platform:
    """
    Detect and return the current operating system platform as a standardized identifier.
    
    Returns:
        Platform: A string or `OtherPlatform` instance representing the detected platform, such as "iOS", "MacOS", "Windows", "Android", "Linux", "FreeBSD", "OpenBSD", or "Unknown". If the platform cannot be matched to a known type, returns an `OtherPlatform` with the raw platform string.
    """
    try:
        system = platform.system().lower()
        platform_name = platform.platform().lower()
    except Exception:
        return "Unknown"

    if "iphone" in platform_name or "ipad" in platform_name:
        # Tested using Python3IDE on an iPhone 11 and Pythonista on an iPad 7
        # system is Darwin and platform_name is a string like:
        # - Darwin-21.6.0-iPhone12,1-64bit
        # - Darwin-21.6.0-iPad7,11-64bit
        return "iOS"

    if system == "darwin":
        return "MacOS"

    if system == "windows":
        return "Windows"

    if "android" in platform_name:
        # Tested using Pydroid 3
        # system is Linux and platform_name is a string like 'Linux-5.10.81-android12-9-00001-geba40aecb3b7-ab8534902-aarch64-with-libc'
        return "Android"

    if system == "linux":
        # https://distro.readthedocs.io/en/latest/#distro.id
        distro_id = distro.id()
        if distro_id == "freebsd":
            return "FreeBSD"

        if distro_id == "openbsd":
            return "OpenBSD"

        return "Linux"

    if platform_name:
        return OtherPlatform(platform_name)

    return "Unknown"


@lru_cache(maxsize=None)
def platform_headers(version: str, *, platform: Platform | None) -> Dict[str, str]:
    """
    Return a dictionary of platform-specific HTTP headers for API requests.
    
    Parameters:
        version (str): The package version to include in the headers.
        platform (Platform | None): The platform identifier; if None, the current platform is detected.
    
    Returns:
        Dict[str, str]: A dictionary of headers describing language, package version, OS, architecture, and Python runtime.
    """
    return {
        "X-Stainless-Lang": "python",
        "X-Stainless-Package-Version": version,
        "X-Stainless-OS": str(platform or get_platform()),
        "X-Stainless-Arch": str(get_architecture()),
        "X-Stainless-Runtime": get_python_runtime(),
        "X-Stainless-Runtime-Version": get_python_version(),
    }


class OtherArch:
    def __init__(self, name: str) -> None:
        """
        Initialize the object with the given name.
        
        Parameters:
            name (str): The name to associate with this instance.
        """
        self.name = name

    @override
    def __str__(self) -> str:
        """
        Return a string representation of the object in the format 'other:{name}'.
        """
        return f"other:{self.name}"


Arch = Union[OtherArch, Literal["x32", "x64", "arm", "arm64", "unknown"]]


def get_python_runtime() -> str:
    """
    Return the name of the current Python runtime implementation.
    
    Returns:
        str: The Python implementation name (e.g., 'CPython', 'PyPy'), or 'unknown' if detection fails.
    """
    try:
        return platform.python_implementation()
    except Exception:
        return "unknown"


def get_python_version() -> str:
    """
    Return the current Python interpreter version as a string.
    
    If the version cannot be determined, returns "unknown".
    """
    try:
        return platform.python_version()
    except Exception:
        return "unknown"


def get_architecture() -> Arch:
    """
    Detect and return the current system's CPU architecture as an `Arch` type.
    
    Returns:
        Arch: The detected architecture, such as "arm64", "arm", "x64", "x32", or an `OtherArch` instance for unrecognized values. Returns "unknown" if detection fails.
    """
    try:
        machine = platform.machine().lower()
    except Exception:
        return "unknown"

    if machine in ("arm64", "aarch64"):
        return "arm64"

    # TODO: untested
    if machine == "arm":
        return "arm"

    if machine == "x86_64":
        return "x64"

    # TODO: untested
    if sys.maxsize <= 2**32:
        return "x32"

    if machine:
        return OtherArch(machine)

    return "unknown"


def _merge_mappings(
    obj1: Mapping[_T_co, Union[_T, Omit]],
    obj2: Mapping[_T_co, Union[_T, Omit]],
) -> Dict[_T_co, _T]:
    """
    Merge two mappings, excluding keys whose values are instances of `Omit`.
    
    If a key exists in both mappings, the value from the second mapping is used. Keys with values of type `Omit` are omitted from the result.
    
    Returns:
        A dictionary containing merged key-value pairs, excluding any with `Omit` values.
    """
    merged = {**obj1, **obj2}
    return {key: value for key, value in merged.items() if not isinstance(value, Omit)}
