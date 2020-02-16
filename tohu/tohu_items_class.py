import attr
import re

from typing import List

__all__ = ["make_tohu_items_class", "derive_tohu_items_class_name"]


def make_tohu_items_class(clsname: str, field_names: List[str]):
    """
    Parameters
    ----------
    clsname: str
        Name of the class to be created.

    field_names: list of str
        Names of the field attributes of the class to be created.
    """
    item_cls = attr.make_class(clsname, {name: attr.ib() for name in field_names}, repr=True, cmp=True, frozen=True)
    func_eq_orig = item_cls.__eq__

    def func_eq_new(self, other):
        """
        Custom __eq__() method which also allows comparisons with
        tuples and dictionaries. This is mostly for convenience
        during testing.
        """

        if isinstance(other, self.__class__):
            return func_eq_orig(self, other)
        else:
            if isinstance(other, tuple):
                return attr.astuple(self) == other
            elif isinstance(other, dict):
                return attr.asdict(self) == other
            elif hasattr(other, "__attrs_attrs__") and self.__class__.__name__ == other.__class__.__name__:
                return attr.asdict(self) == attr.asdict(other)
            else:
                raise TypeError(
                    "Tohu items have types that cannot be compared: "
                    f"{self.__class__.__name__}, {other.__class__.__name__}"
                )

    item_cls.__eq__ = func_eq_new
    item_cls.field_names = field_names
    item_cls.as_dict = lambda self: attr.asdict(self)
    item_cls.as_tuple = lambda self: attr.astuple(self)
    item_cls.is_unset = False
    return item_cls


def derive_tohu_items_class_name(custom_gen_cls_name: str):
    """
    Given the name of a custom generator class, return the name of the associated tohu items class.
    This is derived simply by removing the `...Generator` suffix from the custom generator class name.
    If this class doesn't end with `Generator`, an error is raised.

    Parameters
    ----------
    custom_gen_cls_name : str
        Name of the custom generator class.

    Returns
    -------
    name : str
        Name of the tohu items class associated with the custom generator.
    """
    m = re.match("^(.*)Generator$", custom_gen_cls_name)
    if m:
        return m.group(1)
    else:
        raise ValueError(f"Custom generator class name must end with 'Generator'. Got: {custom_gen_cls_name}")
