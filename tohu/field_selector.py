from abc import ABCMeta, abstractmethod
from collections.abc import Mapping, Sequence
from operator import attrgetter, itemgetter
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


class BaseItemTransformation(metaclass=ABCMeta):
    def __init__(self, func, new_field_names):
        self.func = func
        # self.orig_field_names = orig_field_names
        self.new_field_names = new_field_names

    def __call__(self, x):
        return self.func(x)

    @abstractmethod
    def can_be_applied(self, item_list):
        # assert isinstance(item_list, BaseItemList)
        raise NotImplementedError()


class FieldSelectorNEW(BaseItemTransformation):
    def __init__(self, field_indices, new_field_names):
        assert len(field_indices) == len(new_field_names)

        self.field_indices = field_indices
        func = itemgetter(*field_indices)
        super().__init__(func, new_field_names)

    def can_be_applied(self, item_list):
        return min(self.field_indices) >= 0 and max(self.field_indices) < len(item_list.field_names)
