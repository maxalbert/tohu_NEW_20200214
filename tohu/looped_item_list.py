from string import Formatter
from typing import Optional
from .export import export_to_df, prepare_item_tuples_for_export, export_to_csv_string_or_file


def find_placeholder_variables(filename_pattern: Optional[str]):
    if filename_pattern is None:
        return None
    else:
        formatter = Formatter()
        param_names = [name for (_, name, _, _) in formatter.parse(filename_pattern) if name is not None]
        return param_names


class LoopedItemList:
    def __init__(self, f_get_item_tuple_iterators, *, field_names, tohu_items_class_name):
        # raise NotImplementedError("TODO: how to get item_tuples?")
        self.f_get_item_tuple_iterators = f_get_item_tuple_iterators
        self.field_names = field_names
        self.tohu_items_class_name = tohu_items_class_name
        self.is_cached = False
        self.cached_items_sequence = None

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __iter__(self):
        yield from self.iter_item_tuples()

    def iter_item_tuples(self):
        if self.is_cached:
            yield from self.cached_items_sequence
        else:
            _, items = next(self.f_get_item_tuple_iterators())
            yield from items

    def compute(self):
        self.cached_items_sequence = list(self.iter_item_tuples())
        self.is_cached = True
        return self

    def to_df(self, fields=None, column_names=None, group_by=None):
        if isinstance(group_by, str):
            group_by = [group_by]
        assert isinstance(group_by, (list, tuple)) or group_by is None

        input_field_names = self.field_names
        dataframes = []
        for loop_var_values, item_tuple_iterator in self.f_get_item_tuple_iterators(group_by):
            item_tuples_to_export, fields, column_names = prepare_item_tuples_for_export(
                item_tuple_iterator,
                input_field_names=input_field_names,
                fields_to_select=fields,
                column_names=column_names,
                output_tohu_item_class_name=self.tohu_items_class_name,
            )
            df = export_to_df(item_tuples_to_export, column_names=column_names)
            dataframes.append((loop_var_values, df))

        if group_by is None:
            assert len(dataframes) == 1
            _, df = dataframes[0]
            return df
        else:
            return dataframes

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
        filename_pattern = filename  # alias which better reflects its meaning
        var_names = find_placeholder_variables(filename_pattern)
        input_field_names = self.field_names

        csv_strings = []
        for loop_var_values, item_tuple_iterator in self.f_get_item_tuple_iterators(var_names):
            cur_filename = filename_pattern.format(**loop_var_values) if filename_pattern is not None else None
            item_tuples_to_export, fields, column_names = prepare_item_tuples_for_export(
                item_tuple_iterator,
                input_field_names=input_field_names,
                fields_to_select=fields,
                column_names=column_names,
                output_tohu_item_class_name=self.tohu_items_class_name,
            )
            csv_or_none = export_to_csv_string_or_file(
                cur_filename,
                item_tuples_to_export,
                column_names=column_names,
                sep=sep,
                header=header,
                header_prefix=header_prefix,
            )
            csv_strings.append(csv_or_none)

        if filename is None:
            assert len(csv_strings) == 1
            return csv_strings[0]
