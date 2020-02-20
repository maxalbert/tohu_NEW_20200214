import numpy as np
import warnings
from faker import Faker
from random import Random

from .base import TohuBaseGenerator
from .utils import identity

__all__ = ["Constant", "Boolean", "Integer", "Float", "HashDigest", "FakerGenerator", "SelectOne"]


class Constant(TohuBaseGenerator):
    """
    Generator which produces a constant sequence (repeating the same value indefinitely).
    """

    def __init__(self, value):
        super().__init__()
        self.value = value

    def reset(self, seed):
        """
        Note that the value of the `seed` argument is ignored because
        resetting a Constant generator does not have any effect (since
        it always returns the same element anyway).

        The only reason it accepts this argument is for consistency
        with other tohu generators.
        """
        super().reset(seed)
        return self

    def __next__(self):
        return self.value

    def spawn(self, gen_mapping=None):
        new_gen = Constant(self.value)
        return new_gen


class Boolean(TohuBaseGenerator):
    """
    Generator which produces random boolean values (True or False) with a given probability.
    """

    def __init__(self, p=0.5):
        """
        Parameters
        ----------
        p: float
            The probability that True is returned. Must be between 0.0 and 1.0.
        """
        super().__init__()
        self.p = p
        self.randgen = Random()
        self.dtype = bool

    def reset(self, seed):
        super().reset(seed)
        self.randgen.seed(seed)
        return self

    def __next__(self):
        return self.randgen.random() < self.p

    def spawn(self, gen_mapping=None):
        new_gen = Boolean(p=self.p)
        new_gen._set_state_from(self)
        return new_gen

    def _set_state_from(self, other):
        self.randgen.setstate(other.randgen.getstate())


class Integer(TohuBaseGenerator):
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
        super().__init__()
        self.low = low
        self.high = high
        self.randgen = Random()

    def reset(self, seed):
        super().reset(seed)
        self.randgen.seed(seed)
        return self

    def __next__(self):
        return self.randgen.randint(self.low, self.high)

    def spawn(self, gen_mapping=None):
        new_gen = Integer(self.low, self.high)
        new_gen._set_state_from(self)
        return new_gen

    def _set_state_from(self, other):
        self.randgen.setstate(other.randgen.getstate())


class Float(TohuBaseGenerator):
    """
    Generator which produces random floating point numbers x in the range low <= x <= high.
    """

    def __init__(self, low: float, high: float, ndigits: int = None):
        """
        Parameters
        ----------
        low: integer
            Lower bound (inclusive).
        high: integer
            Upper bound (inclusive).
        ndigits: integer, default None
            Number of digits to which generated numbers should
            be truncated. Default: None (= no truncation).
        """
        super().__init__()
        self.low = low
        self.high = high
        self.randgen = Random()
        self.ndigits = ndigits
        self._maybe_truncate = identity if ndigits is None else lambda x: round(x, ndigits)

    def reset(self, seed):
        super().reset(seed)
        self.randgen.seed(seed)
        return self

    def __next__(self):
        return self._maybe_truncate(self.randgen.uniform(self.low, self.high))

    def spawn(self, gen_mapping=None):
        new_gen = Float(low=self.low, high=self.high, ndigits=self.ndigits)
        new_gen._set_state_from(self)
        return new_gen

    def _set_state_from(self, other):
        self.randgen.setstate(other.randgen.getstate())


class HashDigest(TohuBaseGenerator):
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
        super().__init__()
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
        super().reset(seed)
        self.randgen.seed(seed)
        return self

    def __next__(self):
        val = self.randgen.bytes(self._internal_length)
        return self._maybe_convert_to_uppercase(self._maybe_convert_to_hex(val))

    def spawn(self, gen_mapping=None):
        new_gen = HashDigest(length=self.length, as_bytes=self.as_bytes, lowercase=self.lowercase)
        new_gen._set_state_from(self)
        return new_gen

    def _set_state_from(self, other):
        self.randgen.set_state(other.randgen.get_state())


class FakerGenerator(TohuBaseGenerator):
    """
    Generator which produces random elements using one of the methods supported by faker. [1]

    [1] https://faker.readthedocs.io/
    """

    def __init__(self, method, *, locale=None, **faker_args):
        """
        Parameters
        ----------
        method: string
            Name of the faker provider to use (see [1] for details)
        locale: string
             Locale to use when generating data, e.g. 'en_US' (see [1] for details)
        faker_args:
            Remaining arguments passed to the faker provider (see [1] for details)

        References
        ----------
        [1] https://faker.readthedocs.io/
        """
        super().__init__()
        self.method = method
        self.locale = locale
        self.faker_args = faker_args

        self.fake = Faker(locale=locale)
        self.randgen = getattr(self.fake, method)
        self.fake.seed_instance(None)  # seed instance to ensure we are decoupled from the global random state

    def reset(self, seed):
        super().reset(seed)
        self.fake.seed_instance(seed)
        return self

    def __next__(self):
        return self.randgen(**self.faker_args)

    def spawn(self, gen_mapping=None):
        new_gen = FakerGenerator(method=self.method, locale=self.locale, **self.faker_args)
        new_gen._set_state_from(self)
        return new_gen

    def _set_state_from(self, other):
        self.fake.random.setstate(other.fake.random.getstate())


class SelectOne(TohuBaseGenerator):
    """
    Generator which produces random elements chosen from a fixed sequence of items.
    """

    def __init__(self, items):
        super().__init__()
        self.items = list(items)  #  TOOD: for efficiency, only do this if items is a generator?
        self.randgen = Random()

    def reset(self, seed):
        super().reset(seed)
        self.randgen.seed(seed)

    def __next__(self):
        return self.randgen.choice(self.items)

    def spawn(self, gen_mapping=None):
        new_gen = SelectOne(self.items)
        new_gen._set_state_from(self)
        return new_gen

    def _set_state_from(self, other):
        self.randgen.setstate(other.randgen.getstate())


# PRIMITIVE_GENERATORS = [Constant, Boolean, Integer, Float, HashDigest, FakerGenerator, SelectOne]
EXEMPLAR_PRIMITIVE_GENERATORS = [
    Constant("quux"),
    Boolean(p=0.3),
    Integer(low=100, high=200),
    Float(low=2.0, high=5.0, ndigits=3),
    HashDigest(length=6),
    FakerGenerator(method="name"),
    SelectOne(["aa", "bb", "cc", "dd"]),
]
