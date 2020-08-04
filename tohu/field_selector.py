import re
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from operator import attrgetter

from .logging import logger
from .tohu_items_class import make_tohu_items_class

__all__ = ["FieldSelectorNEW3b", "InvalidFieldError"]


class InvalidFieldError(Exception):
    """
    Custom exception to indicate that the user is trying to extract a non-existing field.
    """


# class FieldSelector:
#     def __init__(
#         self, tohu_items_cls: type, fields: typing.Union[typing.Sequence[str], typing.Mapping[str, str], None] = None
#     ):
#         self.tohu_items_cls = tohu_items_cls
#         if fields is None:
#             self.fields = {name: name for name in self.tohu_items_cls.field_names}
#         elif isinstance(fields, Mapping):
#             self.fields = fields
#         elif isinstance(fields, Sequence) and not isinstance(fields, str):
#             self.fields = {name: name for name in fields}
#         else:  # pragma: no cover
#             raise TypeError(f"Invalid 'fields' argument: {fields}")
#
#         # if not set(self.fields.values()).issubset(self.tohu_items_cls.field_names):
#         #     invalid_fields = [x for x in self.fields.values() if x not in self.tohu_items_cls.field_names]
#         #     valid_fields = self.tohu_items_cls.field_names
#         #     raise InvalidFieldError(f"Invalid fields: {invalid_fields}. Fields must be a subset of: {valid_fields}")
#
#         self.field_selectors = {new_name: attrgetter(orig_name) for new_name, orig_name in self.fields.items()}
#
#     def __call__(self, items: typing.Iterable) -> typing.Iterable:
#         for item in items:
#             yield {name: f(item) for name, f in self.field_selectors.items()}


class BaseItemTransformation(metaclass=ABCMeta):
    def __init__(self, func, new_field_names):
        self.func = func
        # self.orig_field_names = orig_field_names
        self.new_field_names = new_field_names

    def __call__(self, item_stream):
        yield from (self.transform_single_item(x) for x in item_stream)

    @abstractmethod
    def transform_single_item(self, item):
        raise NotImplementedError()  # pragma: no cover

    #
    # @abstractmethod
    # def can_be_applied(self, item_list):
    #     # assert isinstance(item_list, BaseItemList)
    #     raise NotImplementedError()


# class FieldSelectorNEW(BaseItemTransformation):
#     def __init__(self, field_indices, new_field_names):
#         assert len(field_indices) == len(new_field_names)
#
#         self.field_indices = field_indices
#         func = itemgetter(*field_indices)
#         super().__init__(func, new_field_names)
#
#     def can_be_applied(self, item_list):
#         return min(self.field_indices) >= 0 and max(self.field_indices) < len(item_list.field_names)


def get_first_component(fully_qualified_name):
    return fully_qualified_name.split(".")[0]


class FieldSelectorNEW3b(BaseItemTransformation):
    def __init__(self, input_tohu_item_class, fields_to_extract, new_field_names):
        assert (
            (fields_to_extract is None) or (new_field_names is None) or (len(fields_to_extract) == len(new_field_names))
        )

        if fields_to_extract is None:
            fields_to_extract = input_tohu_item_class.field_names
        elif isinstance(fields_to_extract, Sequence) and not isinstance(fields_to_extract, str):
            pass
        else:  # pragma: no cover
            raise TypeError(f"Invalid value for argument 'fields_to_extract': {fields_to_extract}")

        if new_field_names is None:
            new_field_names = fields_to_extract
        elif isinstance(new_field_names, Sequence) and not isinstance(new_field_names, str):
            pass
        else:  # pragma: no cover
            raise TypeError(f"Invalid value for argument 'new_field_names': {new_field_names}")

        if any(["." in name for name in new_field_names]):
            logger.debug(f"Replacing dots in new field name with underscores: {new_field_names}")
            new_field_names = [re.sub("\.", "_", name) for name in new_field_names]

        # Note: for nested fields we can currently only check the first
        # component because we have no information on the data types so if a
        # sub-field name is invalid this will only trigger an error at
        # runtime. Would be nice to keep track of data types too and catch
        # this sooner.
        invalid_fields = [
            get_first_component(name)
            for name in fields_to_extract
            if get_first_component(name) not in input_tohu_item_class.field_names
        ]
        if invalid_fields != []:
            raise InvalidFieldError(
                f"Invalid fields: {invalid_fields}. Fields must be a subset of: {input_tohu_item_class.field_names}"
            )

        output_tohu_item_class = make_tohu_items_class(input_tohu_item_class.__name__, new_field_names)

        select_given_fields = attrgetter(*[name for name in fields_to_extract])
        func = lambda item: output_tohu_item_class(*select_given_fields(item))
        super().__init__(func, new_field_names)

    def transform_single_item(self, x):
        return self.func(x)
