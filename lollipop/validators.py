from __future__ import annotations

from lollipop.errors import ValidationError, ValidationErrorBuilder, \
    ErrorMessagesMixin
from lollipop.compat import string_types, iteritems
from lollipop.utils import make_context_aware, is_sequence, identity
import re
import typing as t


__all__ = [
    'Validator',
    'Predicate',
    'Range',
    'Length',
    'NoneOf',
    'AnyOf',
    'Regexp',
    'Unique',
    'Each',
]


class Validator(ErrorMessagesMixin, object):
    """Base class for all validators.

    Validator is used by types to validate data during deserialization. Validator
    class should define `__call__` method with either one or two arguments. In both
    cases, first argument is value being validated. In case of two arguments, the
    second one is the context. If given value fails validation, `__call__` method
    should raise :exc:`~lollipop.errors.ValidationError`. Return value is always
    ignored.
    """

    def __call__(self, value: t.Any, context: t.Any = None) -> None:
        """Validate value. In case of errors, raise
        :exc:`~lollipop.errors.ValidationError`. Return value is always ignored.
        """
        raise NotImplementedError()


class Predicate(Validator):
    """Validator that succeeds if given predicate returns True.

    :param callable predicate: Predicate that takes value and returns True or False.
        One- and two-argument predicates are supported. First argument in both cases
        is value being validated. In case of two arguments, the second one is
        context.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data``.
    """

    default_error_messages: dict[str, str] = {
        'invalid': 'Invalid data',
    }
    predicate: t.Callable[[t.Any, t.Any], bool]
    error: str | None

    def __init__(self, predicate: t.Callable[..., bool],
                 error: str | None = None, **kwargs) -> None:
        super(Predicate, self).__init__(**kwargs)
        self.predicate = make_context_aware(predicate, 1)
        if error is not None:
            self._error_messages['invalid'] = error
        self.error = error

    def __call__(self, value: t.Any, context: t.Any = None) -> None:
        if not self.predicate(value, context):
            self._fail('invalid', data=value)

    def __repr__(self) -> str:
        return '<{klass} predicate={predicate} error={error}>'.format(
            klass=self.__class__.__name__,
            predicate=self.predicate, error=self.error,
        )


class Range(Validator):
    """Validator that checks value is in given range.

    :param int min: Minimum length. If not provided, minimum won't be checked.
    :param int max: Maximum length. If not provided, maximum won't be checked.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data``, ``min`` or ``max``.
    """

    default_error_messages: dict[str, str] = {
        'min': 'Value should be at least {min}',
        'max': 'Value should be at most {max}',
        'range': 'Value should be at least {min} and at most {max}',
    }
    min: int | None
    max: int | None

    def __init__(self, min: int | None = None, max: int | None = None,
                 error: str | None = None, **kwargs) -> None:
        super(Range, self).__init__(**kwargs)
        self.min = min
        self.max = max
        if error is not None:
            for key in ['min', 'max', 'range']:
                self._error_messages[key] = error

    def _fail(self, error_key: str, **kwargs) -> None:
        super(Range, self)._fail(error_key, min=self.min, max=self.max, **kwargs)

    def __call__(self, value: t.Any, context: t.Any = None) -> None:
        if self.min is not None and self.max is not None:
            if value < self.min or value > self.max:
                self._fail('range', data=value)
        elif self.min is not None:
            if value < self.min:
                self._fail('min', data=value)
        elif self.max is not None:
            if value > self.max:
                self._fail('max', data=value)

    def __repr__(self) -> str:
        return '<{klass} {properties}>'.format(
            klass= self.__class__.__name__,
            properties=' '.join(['%s=%s' % (k, repr(v))
                                 for k, v in iteritems({'min': self.min,
                                                        'max': self.max})
                                 if v is not None])
        )


class Length(Validator):
    """Validator that checks value length (using ``len()``) to be in given range.

    :param int exact: Exact length. If provided, ``min`` and ``max`` are not checked.
        If not provided, ``min`` and ``max`` checks are performed.
    :param int min: Minimum length. If not provided, minimum length won't be checked.
    :param int max: Maximum length. If not provided, maximum length won't be checked.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data``, ``length``, ``exact``, ``min`` or ``max``.
    """
    default_error_messages: dict[str, str] = {
        'exact': 'Length should be {exact}',
        'min': 'Length should be at least {min}',
        'max': 'Length should be at most {max}',
        'range': 'Length should be at least {min} and at most {max}',
    }
    exact: int | None
    min: int | None
    max: int | None

    def __init__(self, exact: int | None = None, min: int | None = None, max: int | None = None,
                 error: str | None = None, **kwargs):
        super(Length, self).__init__(**kwargs)
        self.exact = exact
        self.min = min
        self.max = max
        if error is not None:
            for key in ['exact', 'min', 'max', 'range']:
                self._error_messages[key] = error

    def _fail(self, error_key: str, **kwargs) -> None:
        super(Length, self)._fail(error_key, exact=self.exact, min=self.min, max=self.max,
                                  **kwargs)

    def __call__(self, value: t.Any, context: t.Any = None) -> None:
        length = len(value)
        if self.exact is not None:
            if length != self.exact:
                self._fail('exact', data=value, length=length)
        elif self.min is not None and self.max is not None:
            if length < self.min or length > self.max:
                self._fail('range', data=value, length=length)
        elif self.min is not None:
            if length < self.min:
                self._fail('min', data=value, length=length)
        elif self.max is not None:
            if length > self.max:
                self._fail('max', data=value, length=length)

    def __repr__(self) -> str:
        if self.exact is not None:
            return '<{klass} exact={exact}>'.format(
                klass=self.__class__.__name__,
                exact=self.exact
            )
        else:
            return '<{klass} {properties}>'.format(
                klass= self.__class__.__name__,
                properties=' '.join(['%s=%s' % (k, repr(v))
                                    for k, v in iteritems({'min': self.min,
                                                           'max': self.max})
                                    if v is not None])
            )


class NoneOf(Validator):
    """Validator that succeeds if ``value`` is not a member of given ``values``.

    :param iterable values: A sequence of invalid values.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data`` and ``values``.
    """

    default_error_messages: dict[str, str] = {
        'invalid': 'Invalid data',
    }
    values: t.Iterable[t.Any]

    def __init__(self, values: t.Iterable[t.Any], error: str | None = None, **kwargs) -> None:
        super(NoneOf, self).__init__(**kwargs)
        self.values = values
        if error is not None:
            self._error_messages['invalid'] = error

    def __call__(self, value: t.Any, context: t.Any = None) -> None:
        if value in self.values:
            self._fail('invalid', data=value, values=self.values)

    def __repr__(self) -> str:
        return '<{klass} {values}>'.format(
            klass=self.__class__.__name__,
            values=repr(self.values),
        )


class AnyOf(Validator):
    """Validator that succeeds if ``value`` is a member of given ``choices``.

    :param iterable choices: A sequence of allowed values.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data`` and ``choices``.
    """

    default_error_messages: dict[str, str] = {
        'invalid': 'Invalid choice',
    }
    choices: t.Iterable[t.Any]

    def __init__(self, choices: t.Iterable[t.Any], error: str | None = None, **kwargs) -> None:
        super(AnyOf, self).__init__(**kwargs)
        self.choices = choices
        if error is not None:
            self._error_messages['invalid'] = error

    def __call__(self, value: t.Any, context: t.Any = None) -> None:
        if value not in self.choices:
            self._fail('invalid', data=value, choices=self.choices)

    def __repr__(self) -> str:
        return '<{klass} {choices}>'.format(
            klass=self.__class__.__name__,
            choices=repr(self.choices),
        )


class Regexp(Validator):
    """Validator that succeeds if ``value`` matches given ``regex``.

    :param str regexp: Regular expression string.
    :param int flags: Regular expression flags, e.g. re.IGNORECASE.
        Not used if regexp is not a string.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data`` and ``regexp``.
    """

    default_error_messages: dict[str, str] = {
        'invalid': 'String does not match expected pattern',
    }
    regexp: re.Pattern[str]

    def __init__(self, regexp: str | re.Pattern[str], flags: int = 0,
                 error: str | None = None, **kwargs) -> None:
        super(Regexp, self).__init__(**kwargs)
        if isinstance(regexp, str) or isinstance(regexp, string_types):
            regexp = re.compile(regexp, flags)
        self.regexp = regexp
        if error is not None:
            self._error_messages['invalid'] = error

    def __call__(self, value: t.Any, context: t.Any = None) -> None:
        if self.regexp.match(value) is None:
            self._fail('invalid', data=value, regexp=self.regexp.pattern)

    def __repr__(self) -> str:
        return '<{klass} {regexp}>'.format(
            klass=self.__class__.__name__,
            regexp=self.regexp.pattern,
        )


class Unique(Validator):
    """Validator that succeeds if items in collection are unqiue.
    By default items themselves should be unique, but you can specify a custom
    function to get uniqueness key from items.

    :param callable key: Function to get uniqueness key from items.
    :param str error: Erorr message in case item appear more than once.
        Can be interpolated with ``data`` (the item that is not unique)
        and ``key`` (uniquness key that is not unique).
    """

    default_error_messages: dict[str, str] = {
        'invalid': 'Value should be collection',
        'unique': 'Values are not unique',
    }
    key: t.Callable[[t.Any], t.Any]

    def __init__(self, key: t.Callable[[t.Any], t.Any] = identity, error: str | None = None, **kwargs) -> None:
        super(Unique, self).__init__(**kwargs)
        self.key = key
        if error is not None:
            self._error_messages['unique'] = error

    def __call__(self, value: t.Any, context: t.Any = None) -> None:
        if not is_sequence(value):
            self._fail('invalid')

        seen = set()
        for item in value:
            key = self.key(item)
            if key in seen:
                self._fail('unique', data=item, key=key)
            seen.add(key)

    def __repr__(self) -> str:
        return '<{klass}>'.format(klass=self.__class__.__name__)


class Each(Validator):
    """Validator that takes a list of validators and applies all of them to
    each item in collection.

    :param validators: Validator or list of validators to run against each element
        of collection.
    """
    default_error_messages: dict[str, str] = {
        'invalid': 'Value should be collection',
    }
    validators: list[Validator]

    def __init__(self, validators: list[Validator] | Validator, **kwargs) -> None:
        super(Validator, self).__init__(**kwargs)
        if not isinstance(validators, t.Sequence):
            validators = [validators]
        self.validators = validators

    def __call__(self, value: t.Any, context: t.Any = None) -> None:
        if not is_sequence(value):
            self._fail('invalid', data=value)

        error_builder = ValidationErrorBuilder()

        for idx, item in enumerate(value):
            for validator in self.validators:
                try:
                    validator(item)
                except ValidationError as ve:
                    error_builder.add_errors({idx: ve.messages})

        error_builder.raise_errors()

    def __repr__(self) -> str:
        return "<{klass} {validators!r}>".format(
            klass=self.__class__.__name__,
            validators=self.validators,
        )
