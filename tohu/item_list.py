import pandas as pd
from typing import Union, List, Sequence, Dict, Type
from .field_selector import FieldSelector


class ItemList:
    """
    Represents a list of items as produced by calling `generate()` on a custom generator.

    It acts as an intermediary data structure which allows to conveniently explore items
    produced by a custom generator and export them to different formats while working
    interactively.
    """

    def __init__(self, items: List, tohu_items_cls: Type):
        assert isinstance(items, list)
        self.items = items
        self.num_items = len(self.items)
        self.tohu_items_cls = tohu_items_cls

    def __repr__(self):
        return f"<ItemList containing {self.num_items} items>"

    def __len__(self):
        return self.num_items

    def __iter__(self):
        return iter(self.items)

    def to_df(self, fields: Union[Sequence[str], Dict[str, str]] = None):
        """
        Convert list of items to a pandas dataframe.

        Each item is exported as a separate row, with the columns representing the fields.

        Parameters
        ----------
        fields : list or dict, default None
            If given, this allows to specify a subset of fields to export,
            and to rearrange the order. If `fields` is a dictionary, its
            items should be of the form {<new_colname>: <field_name>},
            and this allows to specify different names for the columns of
            the resulting dataframes than the existing field names.

        Returns
        -------
        result : pandas.DataFrame
        """
        fs = FieldSelector(self.tohu_items_cls, fields=fields)
        df = pd.DataFrame(fs(self.items), columns=fs.fields)
        return df

    def head(self, n: int = 5):
        """
        Return the first `n` rows after exporting items to a pandas dataframe.

        Parameters
        ----------
        n : int, default 5
            Number of rows to return.
        """
        return self.to_df().head(n)
