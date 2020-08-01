from .export import export_to_df, prepare_item_tuples_for_export


class LoopedItemList:
    def __init__(self, f_get_item_tuple_iterators, *, field_names):
        # raise NotImplementedError("TODO: how to get item_tuples?")
        self.f_get_item_tuple_iterators = f_get_item_tuple_iterators
        self.field_names = field_names

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

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
            )
            df = export_to_df(item_tuples_to_export, column_names=column_names)
            dataframes.append((loop_var_values, df))

        if group_by is None:
            assert len(dataframes) == 1
            _, df = dataframes[0]
            return df
        else:
            return dataframes
