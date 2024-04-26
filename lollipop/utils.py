from __future__ import annotations

import collections.abc
import inspect
import re
import typing as t
from lollipop.compat import DictMixin, Sequence, Mapping, iterkeys, iteritems, PY2


T = t.TypeVar('T')


def identity(value: T) -> T:
    """Function that returns its argument."""
    return value


def constant(value: T) -> t.Callable[..., T]:
    """Returns function that takes any arguments and always returns given value."""
    def func(*args, **kwargs):
        return value
    return func


def is_sequence(value: t.Any) -> bool:
    """Returns True if value supports list interface; False - otherwise"""
    return isinstance(value, Sequence)


def is_mapping(value: t.Any) -> bool:
    """Returns True if value supports dict interface; False - otherwise"""
    return isinstance(value, Mapping)


def get_arg_count(func: t.Callable) -> int:
    """Calculates a number of arguments based on a signature."""

    if PY2:
        return len(inspect.getargspec(func).args)

    spec = inspect.getfullargspec(func)

    return len(spec.args) + len(spec.kwonlyargs)


# Backward compatibility
is_list = is_sequence
is_dict = is_mapping


def make_context_aware(func: t.Any, numargs: int) -> t.Callable:
    """
    Check if given function has no more arguments than given. If so, wrap it
    into another function that takes extra argument and drops it.
    Used to support user providing callback functions that are not context aware.
    """
    try:
        if inspect.ismethod(func):
            arg_count = get_arg_count(func) - 1
        elif inspect.isfunction(func):
            arg_count = get_arg_count(func)
        elif inspect.isclass(func):
            arg_count = get_arg_count(func.__init__) - 1
        else:
            arg_count = get_arg_count(func.__call__) - 1
    except TypeError:
        arg_count = numargs

    if arg_count <= numargs:
        def normalized(*args):
            return func(*args[:-1])

        return normalized

    return func


def call_with_context(func: t.Callable, context: t.Any, *args) -> t.Callable:
    """
    Check if given function has more arguments than given. Call it with context
    as last argument or without it.
    """
    return make_context_aware(func, len(args))(*args + (context,))


def to_snake_case(s: str) -> str:
    """Converts camel-case identifiers to snake-case."""
    return re.sub('([^_A-Z])([A-Z])', lambda m: m.group(1) + '_' + m.group(2).lower(), s)


def to_camel_case(s: str) -> str:
    """Converts snake-case identifiers to camel-case."""
    return re.sub('_([a-z])', lambda m: m.group(1).upper(), s)


_default: t.Final = object()


class DictWithDefault(DictMixin, object):
    default: t.Any

    def __init__(self, values: dict[t.Any, t.Any] | None = None,
                 default: t.Any = None):
        super(DictWithDefault, self).__init__()
        self._values: dict[t.Any, t.Any] = values or {}
        self.default: t.Any = default

    def __len__(self) -> int:
        return len(self._values)

    def get(self, key: t.Any, default: t.Any = _default) -> t.Any:
        if key in self._values:
            return self._values[key]

        if default is _default:
            default = self.default

        return default

    def __getitem__(self, key: t.Any) -> t.Any:
        if key in self._values:
            return self._values[key]
        return self.default

    def __setitem__(self, key: t.Any, value: t.Any) -> None:
        self._values[key] = value

    def __delitem__(self, key: t.Any) -> None:
        del self._values[key]

    def __iter__(self) -> t.Generator[t.Any, None, None]:
        for key in self._values:
            yield key

    def __contains__(self, key: t.Any) -> bool:
        return key in self._values

    def keys(self) -> collections.abc.KeysView:
        return self._values.keys()

    def iterkeys(self) -> t.Generator[t.Any, None, None]:
        for k in iterkeys(self._values):
            yield k

    def iteritems(self) -> t.Generator[t.Any, None, None]:
        for k, v in iteritems(self._values):
            yield k, v


class OpenStruct(DictMixin):
    """A dictionary that also allows accessing values through object attributes."""
    def __init__(self, data: dict[t.Any, t.Any] | None = None):
        self.__dict__.update({'_data': data or {}})

    def __getitem__(self, key: t.Any) -> t.Any:
        return self._data[key]

    def __setitem__(self, key: t.Any, value: t.Any) -> None:
        self._data[key] = value

    def __delitem__(self, key: t.Any) -> None:
        del self._data[key]

    def __iter__(self) -> t.Generator[t.Any, None, None]:
        for key in self._data:
            yield key

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: t.Any) -> bool:
        return key in self._data

    def keys(self) -> collections.abc.KeysView:
        return self._data.keys()

    def iterkeys(self) -> t.Generator[t.Any, None, None]:
        for k in iterkeys(self._data):
            yield k

    def iteritems(self) -> t.Generator[t.Any, None, None]:
        for k, v in iteritems(self._data):
            yield k, v

    def __hasattr__(self, name: t.Any) -> bool:
        return name in self._data

    def __getattr__(self, name: t.Any) -> t.Any:
        if name not in self._data:
            raise AttributeError(name)
        return self._data[name]

    def __setattr__(self, name: t.Any, value: t.Any) -> None:
        self._data[name] = value

    def __delattr__(self, name: t.Any) -> None:
        if name not in self._data:
            raise AttributeError(name)
        del self._data[name]

    def __repr__(self) -> str:
        return '<%s %s>' % (
            self.__class__.__name__,
            ' '.join('%s=%s' % (k, repr(v)) for k, v in self._data.iteritems()),
        )
