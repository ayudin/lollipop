from __future__ import annotations

import sys
import typing as t

PY2: t.Final[bool] = int(sys.version_info[0]) == 2
PY26: t.Final[bool] = PY2 and int(sys.version_info[1]) < 7

if PY2:
    string_types = (str, unicode)
    int_types = (int, long)
    unicode = unicode
    basestring = basestring
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
else:
    string_types: tuple[type] = (str,)
    int_types: tuple[type] = (int,)
    unicode: type = str
    basestring: tuple = (str, bytes)
    iterkeys: t.Callable = lambda d: d.keys()
    itervalues: t.Callable = lambda d: d.values()
    iteritems: t.Callable = lambda d: d.items()

if PY26:
    from .ordereddict import OrderedDict
    from UserDict import DictMixin  # type: ignore
else:
    from collections import OrderedDict  # type: ignore
    try:
        from collections import (
            MutableMapping as DictMixin,
            Mapping,
            Sequence)
    except ImportError:
        from collections.abc import (
            MutableMapping as DictMixin,
            Mapping,
            Sequence)
