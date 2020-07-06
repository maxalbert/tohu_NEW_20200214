from abc import ABCMeta, abstractmethod
from operator import itemgetter
from .export import export_to_df, export_to_csv_file, export_to_csv_string
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
    def __init__(self, f_get_item_tuple_stream_iterator, num_items, field_names, tohu_items_class_name):
        self.f_get_item_tuple_stream_iterator = f_get_item_tuple_stream_iterator
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
            yield from self.f_get_item_tuple_stream_iterator()

    def compute(self):
        self.is_cached = True
        self.cached_items_sequence = list(self.f_get_item_tuple_stream_iterator())
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
        field_indices = [self.field_names.index(x) for x in fields]
        new_field_names = [self.field_names[idx] for idx in field_indices]
        fs = FieldSelector(field_indices, new_field_names=new_field_names)
        return self.apply_transformation(fs)

    def to_df(self, fields=None, column_names=None):
        assert isinstance(fields, (list, tuple)) or fields is None

        if fields is not None:
            item_list_to_export = self.select_fields(fields)
        else:
            item_list_to_export = self
            fields = self.field_names

        column_names = column_names or fields
        print(f"[DDD] column_names={column_names}")
        assert len(column_names) == len(fields)

        return export_to_df(item_list_to_export.iter_item_tuples(), column_names=column_names)

    def to_csv(self, filename=None, sep=",", header=True, header_prefix=""):
        if filename is None:
            return export_to_csv_string(
                self.iter_item_tuples(), self.field_names, sep=sep, header=header, header_prefix=header_prefix
            )
        else:
            export_to_csv_file(
                filename, self.iter_item_tuples(), self.field_names, sep=sep, header=header, header_prefix=header_prefix
            )
