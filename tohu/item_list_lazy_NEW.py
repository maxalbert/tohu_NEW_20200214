from typing import List, Optional
from .export import export_to_df, export_to_csv_string_or_file
from .field_selector import FieldSelectorNEW3b
from .tohu_items_class import make_tohu_items_class


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
        yield from self.iter_item_tuples()

    def iter_item_tuples(self):
        if self.is_cached:
            yield from self.cached_items_sequence
        else:
            yield from self.f_get_item_tuple_iterator()

    def compute(self):
        self.cached_items_sequence = list(self.iter_item_tuples())
        self.is_cached = True
        return self

    def apply_transformation(self, func_transform_stream):
        def make_new_item_tuples_iterator():
            yield from func_transform_stream(self.iter_item_tuples())

        return LazyItemListNEW(
            make_new_item_tuples_iterator,
            num_items=self.num_items,
            field_names=func_transform_stream.new_field_names,
            tohu_items_class_name=self.tohu_items_class_name,
        )

    def select_fields(self, fields):
        assert isinstance(fields, (list, tuple))
        fs = FieldSelectorNEW3b(self.tohu_items_class, fields, new_field_names=fields)
        return self.apply_transformation(fs)

    def _prepare_items_for_export(self, fields, column_names):
        assert isinstance(fields, (list, tuple)) or fields is None
        assert isinstance(column_names, (list, tuple)) or column_names is None

        if fields is None:
            item_list_to_export = self
            fields = self.field_names
        else:
            item_list_to_export = self.select_fields(fields)

        item_tuples_to_export = item_list_to_export.iter_item_tuples()
        column_names = column_names or fields or self.field_names
        assert len(column_names) == len(fields)

        return item_tuples_to_export, fields, column_names

    def to_df(self, fields: Optional[List[str]] = None, column_names: Optional[List[str]] = None):
        item_tuples_to_export, fields, column_names = self._prepare_items_for_export(fields, column_names)
        return export_to_df(item_tuples_to_export, column_names=column_names)

    def head(self, n: int = 5):
        """
        Return the first `n` rows after exporting items to a pandas dataframe.

        Parameters
        ----------
        n : int, default 5
            Number of rows to return.
        """
        return self.to_df().head(n)

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
