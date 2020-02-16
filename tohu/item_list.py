import pandas as pd
from .field_selector import FieldSelector


class ItemList:
    """
    Represents a list of items as produced by calling `generate()` on a custom generator.

    It acts as an intermediary data structure which allows to conveniently explore items
    produced by a custom generator and export them to different formats while working
    interactively.
    """

    def __init__(self, items, tohu_items_cls):
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

    def to_df(self, fields=None):
        fs = FieldSelector(self.tohu_items_cls, fields=fields)
        df = pd.DataFrame(fs(self.items), columns=fs.fields)
        return df
