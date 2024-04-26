from __future__ import annotations

from lollipop.types import Type
import typing as t


__all__ = [
    'TypeRegistry',
]


TType = t.TypeVar('TType', bound=Type)


class TypeRef(Type, t.Generic[TType]):
    _get_type: t.Callable[[], TType]
    _inner_type: TType | None

    def __init__(self, get_type: t.Callable[[], TType]):
        super(TypeRef, self).__init__()
        self._get_type = get_type
        self._inner_type = None

    @property
    def inner_type(self) -> TType:
        if self._inner_type is None:
            self._inner_type = self._get_type()
        return self._inner_type

    def load(self, *args, **kwargs) -> t.Any:
        return self.inner_type.load(*args, **kwargs)

    def dump(self, *args, **kwargs) -> t.Any:
        return self.inner_type.dump(*args, **kwargs)

    def __hasattr__(self, name: str) -> bool:
        return hasattr(self.inner_type, name)

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self.inner_type, name)


class TypeRegistry(object):
    """Storage for type instances with ability to get type instance proxy with
    delayed type resolution for implementing mutual cross-references.

    Example: ::

        TYPES = TypeRegistry()

        PersonType = TYPES.add('Person', lt.Object({
            'name': lt.String(),
            'books': lt.List(lt.Object(TYPES['Book'], exclude='author')),
        }, constructor=Person))

        BookType = TYPES.add('Book', lt.Object({
            'title': lt.String(),
            'author': lt.Object(TYPES['Person'], exclude='books'),
        }, constructor=Book))
    """
    _types: dict[str, Type]

    def __init__(self):
        super(TypeRegistry, self).__init__()
        self._types = {}

    def add(self, name: str, a_type: Type) -> Type:
        if name in self._types:
            raise ValueError('Type with name "%s" is already registered' % name)
        self._types[name] = a_type
        return a_type

    def _get(self, name: str) -> Type:
        if name not in self._types:
            raise KeyError('Type with name "%s" is not registered' % name)
        return self._types[name]

    def get(self, name: str) -> TypeRef:
        return TypeRef(lambda: self._get(name))

    def __getitem__(self, key: str) -> TypeRef:
        return self.get(key)
