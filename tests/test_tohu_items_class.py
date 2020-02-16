import pytest

from .context import tohu
from tohu.tohu_items_class import derive_tohu_items_class_name


def test_raises_error_if_class_name_does_not_end_with_generator():
    with pytest.raises(ValueError, match="Custom generator class name must end with 'Generator'"):
        derive_tohu_items_class_name("Quux")
