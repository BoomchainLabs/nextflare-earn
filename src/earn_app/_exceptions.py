# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

__all__ = [
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
]


class EarnAppError(Exception):
    pass


class APIError(EarnAppError):
    message: str
    request: httpx.Request

    body: object | None
    """The API response body.

    If the API responded with a valid JSON structure then this property will be the
    decoded result.

    If it isn't a valid JSON structure then this will be the raw response.

    If there was no response associated with this error then it will be `None`.
    """

    def __init__(self, message: str, request: httpx.Request, *, body: object | None) -> None:  # noqa: ARG002
        """
        Initialize an APIError with a message, the originating HTTP request, and optional response body.
        
        Parameters:
            message (str): Description of the API error.
            request (httpx.Request): The HTTP request that triggered the error.
            body (object | None): The API response body, which may be parsed JSON, raw data, or None.
        """
        super().__init__(message)
        self.request = request
        self.message = message
        self.body = body


class APIResponseValidationError(APIError):
    response: httpx.Response
    status_code: int

    def __init__(self, response: httpx.Response, body: object | None, *, message: str | None = None) -> None:
        """
        Initialize an APIResponseValidationError for schema validation failures in API responses.
        
        Parameters:
            response (httpx.Response): The HTTP response object that failed validation.
            body (object | None): The response body, either parsed or raw, associated with the error.
            message (str | None, optional): Custom error message. Defaults to a standard schema validation error message.
        """
        super().__init__(message or "Data returned by API invalid for expected schema.", response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class APIStatusError(APIError):
    """Raised when an API response has a status code of 4xx or 5xx."""

    response: httpx.Response
    status_code: int

    def __init__(self, message: str, *, response: httpx.Response, body: object | None) -> None:
        """
        Initialize an APIStatusError for HTTP responses with error status codes.
        
        Parameters:
            message (str): Description of the error.
            response (httpx.Response): The HTTP response object associated with the error.
            body (object | None): The parsed response body or raw data, if available.
        """
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class APIConnectionError(APIError):
    def __init__(self, *, message: str = "Connection error.", request: httpx.Request) -> None:
        """
        Initialize an APIConnectionError for connection-related issues.
        
        Parameters:
            message (str): Optional error message describing the connection error.
            request (httpx.Request): The HTTP request that triggered the connection error.
        """
        super().__init__(message, request, body=None)


class APITimeoutError(APIConnectionError):
    def __init__(self, request: httpx.Request) -> None:
        """
        Initialize a timeout error for an API request.
        
        Parameters:
            request (httpx.Request): The HTTP request that timed out.
        """
        super().__init__(message="Request timed out.", request=request)


class BadRequestError(APIStatusError):
    status_code: Literal[400] = 400  # pyright: ignore[reportIncompatibleVariableOverride]


class AuthenticationError(APIStatusError):
    status_code: Literal[401] = 401  # pyright: ignore[reportIncompatibleVariableOverride]


class PermissionDeniedError(APIStatusError):
    status_code: Literal[403] = 403  # pyright: ignore[reportIncompatibleVariableOverride]


class NotFoundError(APIStatusError):
    status_code: Literal[404] = 404  # pyright: ignore[reportIncompatibleVariableOverride]


class ConflictError(APIStatusError):
    status_code: Literal[409] = 409  # pyright: ignore[reportIncompatibleVariableOverride]


class UnprocessableEntityError(APIStatusError):
    status_code: Literal[422] = 422  # pyright: ignore[reportIncompatibleVariableOverride]


class RateLimitError(APIStatusError):
    status_code: Literal[429] = 429  # pyright: ignore[reportIncompatibleVariableOverride]


class InternalServerError(APIStatusError):
    pass
