import pandas as pd

from io import StringIO
from .field_selector import FieldSelectorNEW

__all__ = ["export_to_df"]

#
# Helper functions
#


def select_fields(item_tuples, input_field_names, fields_to_select):
    assert isinstance(fields_to_select, (list, tuple))
    field_indices = [input_field_names.index(x) for x in fields_to_select]
    new_field_names = [input_field_names[idx] for idx in field_indices]
    fs = FieldSelectorNEW(field_indices, new_field_names=new_field_names)

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


#
# Export to pandas dataframe
#


def export_to_df(input_tuples, column_names):
    df = pd.DataFrame(input_tuples, columns=column_names)
    return df


#
# Export to CSV string/file
#


def export_to_csv_stream(stream, input_tuples, column_names, sep=",", header=True, header_prefix=""):
    if not header:
        header = ""
    elif header == True:
        header = header_prefix + sep.join(column_names) + "\n"
    elif isinstance(header, str):
        header = header + "\n"
    else:
        raise TypeError("Invalid `header` argument")

    stream.write(header)
    for row_tuple in input_tuples:
        print(sep.join(str(x) for x in row_tuple), file=stream)


def export_to_csv_string(input_tuples, *, column_names, sep=",", header=True, header_prefix=""):
    with StringIO() as s:
        export_to_csv_stream(s, input_tuples, column_names, sep, header, header_prefix)
        return s.getvalue()


def export_to_csv_file(filename, input_tuples, *, column_names, sep=",", header=True, header_prefix=""):
    with open(filename, "w") as f:
        export_to_csv_stream(f, input_tuples, column_names, sep, header, header_prefix)


def export_to_csv_string_or_file(
    optional_filename, input_tuples, *, column_names, sep=",", header=True, header_prefix=""
):
    if optional_filename is None:
        return export_to_csv_string(
            input_tuples, column_names=column_names, sep=sep, header=header, header_prefix=header_prefix
        )
    else:
        export_to_csv_file(
            optional_filename,
            input_tuples,
            column_names=column_names,
            sep=sep,
            header=header,
            header_prefix=header_prefix,
        )


#
# Export to PostgreSQL table
#

# TODO: implement me!
