from __future__ import annotations

from typing import Any
from typing_extensions import override

from ._proxy import LazyProxy


class ResourcesProxy(LazyProxy[Any]):
    """A proxy for the `earn_app.resources` module.

    This is used so that we can lazily import `earn_app.resources` only when
    needed *and* so that users can just import `earn_app` and reference `earn_app.resources`
    """

    @override
    def __load__(self) -> Any:
        """
        Dynamically imports and returns the `earn_app.resources` module when accessed through the proxy.
        
        Returns:
            The imported `earn_app.resources` module.
        """
        import importlib

        mod = importlib.import_module("earn_app.resources")
        return mod


resources = ResourcesProxy().__as_proxied__()
