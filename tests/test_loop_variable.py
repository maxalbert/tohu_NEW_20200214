import pytest

from .context import tohu
from tohu.looping_NEW_2 import LoopVariable


@pytest.mark.parametrize("values", [True, "some_string", 12345])
def test_values_arg_must_be_of_type_sequence(values):
    with pytest.raises(TypeError, match="Argument `values` must be a list, tuple, or similar sequence type"):
        LoopVariable(name="foo", values=values)
