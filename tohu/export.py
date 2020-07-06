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


def export_to_csv_stream(stream, input_tuples, field_names, sep=",", header=True, header_prefix=""):
    if not header:
        header = ""
    elif header == True:
        header = header_prefix + sep.join(field_names) + "\n"
    elif isinstance(header, str):
        header = header + "\n"
    else:
        raise TypeError("Invalid `header` argument")

    stream.write(header)
    for row_tuple in input_tuples:
        print(sep.join(str(x) for x in row_tuple), file=stream)


def export_to_csv_string(input_tuples, field_names, sep=",", header=True, header_prefix=""):
    with StringIO() as s:
        export_to_csv_stream(s, input_tuples, field_names, sep, header, header_prefix)
        return s.getvalue()


def export_to_csv_file(filename, input_tuples, field_names, sep=",", header=True, header_prefix=""):
    with open(filename, "w") as f:
        export_to_csv_stream(f, input_tuples, field_names, sep, header, header_prefix)


#
# Export to PostgreSQL table
#

# TODO: implement me!
