from abc import ABCMeta, abstractmethod
from operator import itemgetter
from .export import export_to_df, export_to_csv_string_or_file
from .tohu_items_class import make_tohu_items_class


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


class FieldSelector(BaseItemTransformation):
    def __init__(self, field_indices, new_field_names):
        assert len(field_indices) == len(new_field_names)

        self.field_indices = field_indices
        func = itemgetter(*field_indices)
        super().__init__(func, new_field_names)

    def can_be_applied(self, item_list):
        return min(self.field_indices) >= 0 and max(self.field_indices) < len(item_list.field_names)


class LazyItemListNEW:
    def __init__(self, f_get_item_tuple_iterator, *, num_items, field_names, tohu_items_class_name):
        self.f_get_item_tuple_iterator = f_get_item_tuple_iterator
        self.num_items = num_items
        self.field_names = field_names
        self.tohu_items_class_name = tohu_items_class_name
        self.tohu_items_class = make_tohu_items_class(tohu_items_class_name, self.field_names)
        self.is_cached = False
        self.cached_items_sequence = None

    def __repr__(self):
        return f"<{self.__class__.__name__} containing {self.num_items} items>"

    def __iter__(self):
        yield from (self.tohu_items_class(*x) for x in self.iter_item_tuples())

    def iter_item_tuples(self):
        if self.is_cached:
            yield from self.cached_items_sequence
        else:
            yield from self.f_get_item_tuple_iterator()

    def compute(self):
        self.is_cached = True
        self.cached_items_sequence = list(self.f_get_item_tuple_iterator())
        return self

    def apply_transformation(self, transformation):
        def make_new_item_tuples_iterator():
            return (transformation(x) for x in self.iter_item_tuples())

        return LazyItemListNEW(
            make_new_item_tuples_iterator,
            num_items=self.num_items,
            field_names=transformation.new_field_names,
            tohu_items_class_name=self.tohu_items_class_name,
        )

    def select_fields(self, fields):
        assert isinstance(fields, (list, tuple))
        field_indices = [self.field_names.index(x) for x in fields]
        new_field_names = [self.field_names[idx] for idx in field_indices]
        fs = FieldSelector(field_indices, new_field_names=new_field_names)
        return self.apply_transformation(fs)

    def _prepare_items_for_export(self, fields, column_names):
        assert isinstance(fields, (list, tuple)) or fields is None
        assert isinstance(column_names, (list, tuple)) or column_names is None

        if fields is None:
            item_tuples_to_export = self.iter_item_tuples()
            fields = self.field_names
        else:
            item_tuples_to_export = self.select_fields(fields).iter_item_tuples()

        column_names = column_names or fields or self.field_names
        assert len(column_names) == len(fields)

        return item_tuples_to_export, fields, column_names

    def to_df(self, fields=None, column_names=None):
        item_tuples_to_export, fields, column_names = self._prepare_items_for_export(fields, column_names)
        return export_to_df(item_tuples_to_export, column_names=column_names)

    def to_csv(self, filename=None, fields=None, column_names=None, sep=",", header=True, header_prefix=""):
        item_tuples_to_export, fields, column_names = self._prepare_items_for_export(fields, column_names)
        return export_to_csv_string_or_file(
            filename,
            item_tuples_to_export,
            column_names=column_names,
            sep=sep,
            header=header,
            header_prefix=header_prefix,
        )


def select_fields(item_tuples, input_field_names, fields_to_select):
    assert isinstance(fields_to_select, (list, tuple))
    field_indices = [input_field_names.index(x) for x in fields_to_select]
    new_field_names = [input_field_names[idx] for idx in field_indices]
    fs = FieldSelector(field_indices, new_field_names=new_field_names)

    return (fs(x) for x in item_tuples)


def prepare_item_tuples_for_export(item_tuples, input_field_names, fields_to_select, column_names):
    assert isinstance(fields_to_select, (list, tuple)) or fields_to_select is None
    assert isinstance(column_names, (list, tuple)) or column_names is None

    if fields_to_select is None:
        item_tuples_to_export = item_tuples
        fields_to_select = input_field_names
    else:
        item_tuples_to_export = select_fields(item_tuples, input_field_names, fields_to_select)

    column_names = column_names or fields_to_select or input_field_names
    assert len(column_names) == len(fields_to_select)

    return item_tuples_to_export, fields_to_select, column_names
