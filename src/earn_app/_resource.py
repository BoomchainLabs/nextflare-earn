# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import anyio

if TYPE_CHECKING:
    from ._client import EarnApp, AsyncEarnApp


class SyncAPIResource:
    _client: EarnApp

    def __init__(self, client: EarnApp) -> None:
        """
        Initialize the SyncAPIResource with a synchronous API client, storing references to its HTTP methods and API list retrieval.
        """
        self._client = client
        self._get = client.get
        self._post = client.post
        self._patch = client.patch
        self._put = client.put
        self._delete = client.delete
        self._get_api_list = client.get_api_list

    def _sleep(self, seconds: float) -> None:
        """
        Pause execution for the specified number of seconds.
        
        Parameters:
            seconds (float): The duration to sleep, in seconds.
        """
        time.sleep(seconds)


class AsyncAPIResource:
    _client: AsyncEarnApp

    def __init__(self, client: AsyncEarnApp) -> None:
        """
        Initialize the AsyncAPIResource with an asynchronous client, assigning its HTTP methods and API list retrieval method to instance variables.
        """
        self._client = client
        self._get = client.get
        self._post = client.post
        self._patch = client.patch
        self._put = client.put
        self._delete = client.delete
        self._get_api_list = client.get_api_list

    async def _sleep(self, seconds: float) -> None:
        """
        Pause asynchronous execution for the specified number of seconds.
        
        Parameters:
            seconds (float): The duration to sleep, in seconds.
        """
        await anyio.sleep(seconds)
