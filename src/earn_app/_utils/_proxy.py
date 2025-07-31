from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Iterable, cast
from typing_extensions import override

T = TypeVar("T")


class LazyProxy(Generic[T], ABC):
    """Implements data methods to pretend that an instance is another instance.

    This includes forwarding attribute access and other methods.
    """

    # Note: we have to special case proxies that themselves return proxies
    # to support using a proxy as a catch-all for any random access, e.g. `proxy.foo.bar.baz`

    def __getattr__(self, attr: str) -> object:
        """
        Forwards attribute access to the proxied object, returning the proxy itself if the proxied object is also a LazyProxy.
        
        Parameters:
            attr (str): The name of the attribute to access.
        
        Returns:
            The value of the requested attribute from the proxied object, or the proxy itself if the proxied object is a LazyProxy.
        """
        proxied = self.__get_proxied__()
        if isinstance(proxied, LazyProxy):
            return proxied  # pyright: ignore
        return getattr(proxied, attr)

    @override
    def __repr__(self) -> str:
        """
        Return the string representation of the proxied object, or the class name if the proxied object is also a LazyProxy.
        """
        proxied = self.__get_proxied__()
        if isinstance(proxied, LazyProxy):
            return proxied.__class__.__name__
        return repr(self.__get_proxied__())

    @override
    def __str__(self) -> str:
        """
        Return the string representation of the proxied object, or the class name if the proxied object is also a LazyProxy.
        """
        proxied = self.__get_proxied__()
        if isinstance(proxied, LazyProxy):
            return proxied.__class__.__name__
        return str(proxied)

    @override
    def __dir__(self) -> Iterable[str]:
        """
        Return the list of attribute names available on the proxied object.
        
        If the proxied object is itself a LazyProxy, returns an empty list.
        """
        proxied = self.__get_proxied__()
        if isinstance(proxied, LazyProxy):
            return []
        return proxied.__dir__()

    @property  # type: ignore
    @override
    def __class__(self) -> type:  # pyright: ignore
        """
        Return the class type of the proxied object, or the proxy's own type if the proxied object cannot be loaded.
        
        If the proxied object is itself a subclass of LazyProxy, returns its type; otherwise, returns the proxied object's class.
        """
        try:
            proxied = self.__get_proxied__()
        except Exception:
            return type(self)
        if issubclass(type(proxied), LazyProxy):
            return type(proxied)
        return proxied.__class__

    def __get_proxied__(self) -> T:
        """
        Returns the underlying proxied object by invoking the subclass-implemented `__load__` method.
        
        Returns:
            T: The object being proxied.
        """
        return self.__load__()

    def __as_proxied__(self) -> T:
        """
        Return the current proxy instance cast to the proxied object type.
        
        Returns:
            The proxy instance, typed as the proxied object.
        """
        return cast(T, self)

    @abstractmethod
    def __load__(self) -> T: """
Load and return the underlying proxied object.

This abstract method must be implemented by subclasses to provide the actual object to be proxied.

Returns:
    T: The object instance being proxied.
"""
...
