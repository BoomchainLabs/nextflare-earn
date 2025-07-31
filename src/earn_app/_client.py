# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, Dict, Union, Mapping, cast
from typing_extensions import Self, Literal, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    NOT_GIVEN,
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
)
from ._utils import is_given, get_async_library
from ._version import __version__
from .resources import stats, token, staking, missions
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import EarnAppError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)
from .resources.users import users

__all__ = [
    "ENVIRONMENTS",
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "EarnApp",
    "AsyncEarnApp",
    "Client",
    "AsyncClient",
]

ENVIRONMENTS: Dict[str, str] = {
    "production": "https://api.slerfhub.xyz/api",
    "environment_1": "https://staging.lerfhub.xyz/api",
}


class EarnApp(SyncAPIClient):
    users: users.UsersResource
    missions: missions.MissionsResource
    staking: staking.StakingResource
    stats: stats.StatsResource
    token: token.TokenResource
    with_raw_response: EarnAppWithRawResponse
    with_streaming_response: EarnAppWithStreamedResponse

    # client options
    api_key: str

    _environment: Literal["production", "environment_1"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "environment_1"] | NotGiven = NOT_GIVEN,
        base_url: str | httpx.URL | None | NotGiven = NOT_GIVEN,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """
        Initializes a new synchronous EarnApp API client with configurable authentication, environment, and HTTP options.
        
        If `api_key` is not provided, it is inferred from the `EARN_APP_API_KEY` environment variable. The API base URL is determined by the `environment` argument, the `EARN_APP_BASE_URL` environment variable, or defaults to the production environment. Raises an error if the API key is missing or if environment and base URL configuration is ambiguous or invalid.
        
        Resource accessors for users, missions, staking, stats, and token management are initialized, along with raw and streaming response wrappers.
        """
        if api_key is None:
            api_key = os.environ.get("EARN_APP_API_KEY")
        if api_key is None:
            raise EarnAppError(
                "The api_key client option must be set either by passing api_key to the client or by setting the EARN_APP_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("EARN_APP_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `EARN_APP_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.users = users.UsersResource(self)
        self.missions = missions.MissionsResource(self)
        self.staking = staking.StakingResource(self)
        self.stats = stats.StatsResource(self)
        self.token = token.TokenResource(self)
        self.with_raw_response = EarnAppWithRawResponse(self)
        self.with_streaming_response = EarnAppWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        """
        Return a Querystring instance configured to format array parameters as comma-separated values.
        """
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        """
        Return the authorization headers required for API requests using the configured API key.
        
        Returns:
            dict: A dictionary containing the Bearer token authorization header.
        """
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        """
        Return the default HTTP headers for the client, including a header indicating synchronous operation and any custom headers.
        """
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "environment_1"] | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance with the same configuration as the current client, allowing selective overrides for authentication, environment, base URL, timeout, retries, headers, and query parameters.
        
        Parameters:
            api_key (str, optional): Override the API key for authentication.
            environment (Literal["production", "environment_1"], optional): Override the target environment.
            base_url (str or httpx.URL, optional): Override the API base URL.
            timeout (float or Timeout, optional): Override the request timeout.
            max_retries (int, optional): Override the maximum number of retry attempts.
            default_headers (Mapping[str, str], optional): Additional headers to merge with existing headers.
            set_default_headers (Mapping[str, str], optional): Replace all default headers with this mapping.
            default_query (Mapping[str, object], optional): Additional query parameters to merge with existing parameters.
            set_default_query (Mapping[str, object], optional): Replace all default query parameters with this mapping.
            _extra_kwargs (Mapping[str, Any], optional): Additional keyword arguments for advanced customization.
        
        Returns:
            Self: A new client instance with the specified configuration overrides.
        
        Raises:
            ValueError: If both `default_headers` and `set_default_headers` are provided, or if both `default_query` and `set_default_query` are provided.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            environment=environment or self._environment,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        """
        Return an APIStatusError instance corresponding to the HTTP response status code.
        
        Maps common HTTP error status codes to specific exception classes for more granular error handling. Returns a generic APIStatusError if the status code does not match a known type.
        
        Parameters:
            err_msg (str): The error message to include in the exception.
            body (object): The response body associated with the error.
            response (httpx.Response): The HTTP response object.
        
        Returns:
            APIStatusError: An exception instance representing the specific error condition.
        """
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncEarnApp(AsyncAPIClient):
    users: users.AsyncUsersResource
    missions: missions.AsyncMissionsResource
    staking: staking.AsyncStakingResource
    stats: stats.AsyncStatsResource
    token: token.AsyncTokenResource
    with_raw_response: AsyncEarnAppWithRawResponse
    with_streaming_response: AsyncEarnAppWithStreamedResponse

    # client options
    api_key: str

    _environment: Literal["production", "environment_1"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "environment_1"] | NotGiven = NOT_GIVEN,
        base_url: str | httpx.URL | None | NotGiven = NOT_GIVEN,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """
        Initializes a new asynchronous EarnApp API client with configurable authentication, environment, and HTTP options.
        
        If `api_key` is not provided, it is inferred from the `EARN_APP_API_KEY` environment variable. The API base URL is determined by the `environment` argument, the `EARN_APP_BASE_URL` environment variable, or defaults to the production environment. Raises an error if the API key is missing or if environment and base URL configuration is ambiguous or invalid.
        
        Resource accessors for users, missions, staking, stats, and token management are initialized for asynchronous use, along with raw and streaming response wrappers.
        """
        if api_key is None:
            api_key = os.environ.get("EARN_APP_API_KEY")
        if api_key is None:
            raise EarnAppError(
                "The api_key client option must be set either by passing api_key to the client or by setting the EARN_APP_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("EARN_APP_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `EARN_APP_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.users = users.AsyncUsersResource(self)
        self.missions = missions.AsyncMissionsResource(self)
        self.staking = staking.AsyncStakingResource(self)
        self.stats = stats.AsyncStatsResource(self)
        self.token = token.AsyncTokenResource(self)
        self.with_raw_response = AsyncEarnAppWithRawResponse(self)
        self.with_streaming_response = AsyncEarnAppWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        """
        Return a Querystring instance configured to format array parameters as comma-separated values.
        """
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        """
        Return the authorization headers required for API requests using the configured API key.
        
        Returns:
            dict: A dictionary containing the Bearer token authorization header.
        """
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        """
        Return the default headers for asynchronous API requests, including an async library identifier and any custom headers.
        """
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "environment_1"] | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance with the same configuration as the current client, allowing selective overrides for authentication, environment, base URL, timeout, retries, headers, and query parameters.
        
        Raises:
            ValueError: If both `default_headers` and `set_default_headers`, or both `default_query` and `set_default_query`, are provided.
            
        Returns:
            A new client instance with the specified options applied.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            environment=environment or self._environment,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        """
        Return an APIStatusError instance corresponding to the HTTP response status code.
        
        Maps common HTTP error status codes to specific exception classes for more granular error handling. Returns a generic APIStatusError if the status code does not match a known type.
        
        Parameters:
            err_msg (str): The error message to include in the exception.
            body (object): The response body associated with the error.
            response (httpx.Response): The HTTP response object.
        
        Returns:
            APIStatusError: An exception instance representing the specific error condition.
        """
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class EarnAppWithRawResponse:
    def __init__(self, client: EarnApp) -> None:
        """
        Initialize resource attributes with raw response variants for the given EarnApp client.
        
        Parameters:
            client (EarnApp): The synchronous EarnApp client whose resources will be wrapped for raw response access.
        """
        self.users = users.UsersResourceWithRawResponse(client.users)
        self.missions = missions.MissionsResourceWithRawResponse(client.missions)
        self.staking = staking.StakingResourceWithRawResponse(client.staking)
        self.stats = stats.StatsResourceWithRawResponse(client.stats)
        self.token = token.TokenResourceWithRawResponse(client.token)


class AsyncEarnAppWithRawResponse:
    def __init__(self, client: AsyncEarnApp) -> None:
        """
        Initialize resource accessors for the asynchronous EarnApp client with raw response variants.
        
        Parameters:
            client (AsyncEarnApp): The asynchronous EarnApp client instance whose resources will be wrapped.
        """
        self.users = users.AsyncUsersResourceWithRawResponse(client.users)
        self.missions = missions.AsyncMissionsResourceWithRawResponse(client.missions)
        self.staking = staking.AsyncStakingResourceWithRawResponse(client.staking)
        self.stats = stats.AsyncStatsResourceWithRawResponse(client.stats)
        self.token = token.AsyncTokenResourceWithRawResponse(client.token)


class EarnAppWithStreamedResponse:
    def __init__(self, client: EarnApp) -> None:
        """
        Initialize resource attributes to provide streaming response variants for the EarnApp client.
        
        Parameters:
            client (EarnApp): The synchronous EarnApp client whose resources will be wrapped for streaming responses.
        """
        self.users = users.UsersResourceWithStreamingResponse(client.users)
        self.missions = missions.MissionsResourceWithStreamingResponse(client.missions)
        self.staking = staking.StakingResourceWithStreamingResponse(client.staking)
        self.stats = stats.StatsResourceWithStreamingResponse(client.stats)
        self.token = token.TokenResourceWithStreamingResponse(client.token)


class AsyncEarnAppWithStreamedResponse:
    def __init__(self, client: AsyncEarnApp) -> None:
        """
        Initialize resource attributes with streaming response variants for the asynchronous EarnApp client.
        
        Parameters:
            client (AsyncEarnApp): The asynchronous EarnApp client instance whose resources will be wrapped for streaming responses.
        """
        self.users = users.AsyncUsersResourceWithStreamingResponse(client.users)
        self.missions = missions.AsyncMissionsResourceWithStreamingResponse(client.missions)
        self.staking = staking.AsyncStakingResourceWithStreamingResponse(client.staking)
        self.stats = stats.AsyncStatsResourceWithStreamingResponse(client.stats)
        self.token = token.AsyncTokenResourceWithStreamingResponse(client.token)


Client = EarnApp

AsyncClient = AsyncEarnApp
