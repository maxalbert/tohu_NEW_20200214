import numpy as np
import warnings
from random import Random
from .utils import identity

__all__ = ["Constant", "Integer", "HashDigest"]


class Constant:
    """
    Generator which produces a constant sequence (repeating the same value indefinitely).
    """

    def __init__(self, value):
        self.value = value

    def reset(self, seed):
        """
        Note that the value of the `seed` argument is ignored because
        resetting a Constant generator does not have any effect (since
        it always returns the same element anyway).

        The only reason it accepts this argument is for consistency
        with other tohu generators.
        """
        return self

    def __next__(self):
        return self.value


class Integer:
    """
    Generator which produces random integers k in the range low <= k <= high.
    """

    def __init__(self, low, high):
        """
        Parameters
        ----------
        low: integer or TohuBaseGenerator
            Lower bound (inclusive).
        high: integer or TohuBaseGenerator
            Upper bound (inclusive).
        """
        self.low = low
        self.high = high
        self.randgen = Random()

    def reset(self, seed):
        self.randgen.seed(seed)
        return self

    def __next__(self):
        return self.randgen.randint(self.low, self.high)


class HashDigest:
    """
    Generator which produces a sequence of hex strings representing hash digest values.
    """

    def __init__(self, *, length, as_bytes=False, lowercase=False):
        """
        Parameters
        ----------
        length: integer or TohuBaseGenerator
            Length of the character strings produced by this generator.
        as_bytes: bool, optional
            If True, return `length` random bytes. If False, return a string
            containing `length` characters (representing the hex values of
            a sequence of  `length/2` random bytes). Note that in the second
            case `length` must be an even number.
        lowercase: bool, optional
            If True, return the hex string using lowercase letters. The default
            uses uppercase letters. This only has an effect if `as_bytes=False`.
        """
        if not as_bytes and (length % 2) != 0:
            raise ValueError(
                f"Length must be an even number if as_bytes=False because it "
                f"represents length = 2 * num_random_bytes. Got: length={length})"
            )

        if lowercase and as_bytes:
            warnings.warn("Ignoring `lowercase=True` because it has no effect when `as_bytes=True`.")

        self.length = length
        if as_bytes:
            self._internal_length = length
        else:
            self._internal_length = length // 2
        self.as_bytes = as_bytes
        self.lowercase = lowercase
        self.randgen = np.random.RandomState()
        self._maybe_convert_to_hex = identity if self.as_bytes else bytes.hex
        self._maybe_convert_to_uppercase = identity if (self.as_bytes or lowercase) else str.upper
        self.dtype = str

    def reset(self, seed):
        self.randgen.seed(seed)
        return self

    def __next__(self):
        val = self.randgen.bytes(self._internal_length)
        return self._maybe_convert_to_uppercase(self._maybe_convert_to_hex(val))
