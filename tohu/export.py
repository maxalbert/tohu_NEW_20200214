import pandas as pd

from io import StringIO

__all__ = ["export_to_df"]


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
