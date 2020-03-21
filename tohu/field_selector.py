from collections.abc import Mapping, Sequence
from operator import attrgetter
import typing

# from .logging import logger

__all__ = ["FieldSelector"]  # , "InvalidFieldError"]


# class InvalidFieldError(Exception):
#     """
#     Custom exception to indicate that the user is trying to extract a non-existing field.
#     """


class FieldSelector:
    def __init__(
        self, tohu_items_cls: type, fields: typing.Union[typing.Sequence[str], typing.Mapping[str, str], None] = None
    ):
        self.tohu_items_cls = tohu_items_cls
        if fields is None:
            self.fields = {name: name for name in self.tohu_items_cls.field_names}
        elif isinstance(fields, Mapping):
            self.fields = fields
        elif isinstance(fields, Sequence) and not isinstance(fields, str):
            self.fields = {name: name for name in fields}
        else:  # pragma: no cover
            raise TypeError(f"Invalid 'fields' argument: {fields}")

        # if not set(self.fields.values()).issubset(self.tohu_items_cls.field_names):
        #     invalid_fields = [x for x in self.fields.values() if x not in self.tohu_items_cls.field_names]
        #     valid_fields = self.tohu_items_cls.field_names
        #     raise InvalidFieldError(f"Invalid fields: {invalid_fields}. Fields must be a subset of: {valid_fields}")

        self.field_selectors = {new_name: attrgetter(orig_name) for new_name, orig_name in self.fields.items()}

    def __call__(self, items: typing.Iterable) -> typing.Iterable:
        for item in items:
            yield {name: f(item) for name, f in self.field_selectors.items()}
