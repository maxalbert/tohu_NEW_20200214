import pytest
import warnings

from .context import tohu
from tohu.primitive_generators import HashDigest


def test_hashdigest_length_must_be_even_for_string_output():
    with pytest.raises(ValueError, match="Length must be an even number if as_bytes=False"):
        _ = HashDigest(length=5, as_bytes=False)


def test_hashdigest_raises_warning_when_combining_as_bytes_with_lowercase():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")  # cause all warnings to be triggered

        _ = HashDigest(length=6, as_bytes=True, lowercase=True)

        assert len(w) == 1
        assert "Ignoring `lowercase=True` because it has no effect when `as_bytes=True`" in str(w[-1].message)
