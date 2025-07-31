import operator
from typing import Any
from typing_extensions import override

from earn_app._utils import LazyProxy


class RecursiveLazyProxy(LazyProxy[Any]):
    @override
    def __load__(self) -> Any:
        """
        Returns the proxy instance itself instead of loading a target object.
        """
        return self

    def __call__(self, *_args: Any, **_kwds: Any) -> Any:
        """
        Raises a RuntimeError if the proxy instance is called as a function.
        """
        raise RuntimeError("This should never be called!")


def test_recursive_proxy() -> None:
    """
    Test that RecursiveLazyProxy returns itself for attribute access and has the expected string representation and type name.
    """
    proxy = RecursiveLazyProxy()
    assert repr(proxy) == "RecursiveLazyProxy"
    assert str(proxy) == "RecursiveLazyProxy"
    assert dir(proxy) == []
    assert type(proxy).__name__ == "RecursiveLazyProxy"
    assert type(operator.attrgetter("name.foo.bar.baz")(proxy)).__name__ == "RecursiveLazyProxy"


def test_isinstance_does_not_error() -> None:
    """
    Test that `isinstance` checks on a proxy raising errors in `__load__` do not propagate exceptions.
    
    Verifies that `isinstance` returns `False` for unrelated types and `True` for the proxy base class, even if the proxy's loading mechanism raises a `RuntimeError`.
    """
    class AlwaysErrorProxy(LazyProxy[Any]):
        @override
        def __load__(self) -> Any:
            raise RuntimeError("Mocking missing dependency")

    proxy = AlwaysErrorProxy()
    assert not isinstance(proxy, dict)
    assert isinstance(proxy, LazyProxy)
