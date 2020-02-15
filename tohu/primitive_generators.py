import hashlib
import numpy as np
import warnings
from faker import Faker
from random import Random
from .utils import identity

__all__ = ["Constant", "Boolean", "Integer", "HashDigest", "FakerGenerator"]


class TohuBaseGenerator:
    """
    Base class for all of tohu's generators.
    """

    def __init__(self):
        self.tohu_name = None

    def __repr__(self):
        clsname = self.__class__.__name__
        name = "" if self.tohu_name is None else f"{self.tohu_name}: "
        return f"<{name}{clsname} (id={self.tohu_id})>"

    def set_tohu_name(self, tohu_name):
        """
        Set this generator's `tohu_name` attribute.

        This is mainly useful for debugging where one can temporarily
        use this at the end of generator definitions to set a name
        that will be displayed in debugging messages. For example:

            g1 = SomeGeneratorClass().set_tohu_name('g1')
            g2 = SomeGeneratorClass().set_tohu_name('g2')
        """
        self.tohu_name = tohu_name
        return self

    @property
    def tohu_id(self):
        """
        Return (truncated) md5 hash representing this generator.
        We truncate the hash simply for readability, as this is
        purely intended for debugging purposes and the risk of
        any collisions will be negligible.
        """
        myhash = hashlib.md5(str(id(self)).encode()).hexdigest()
        return myhash[:6]


class Constant(TohuBaseGenerator):
    """
    Generator which produces a constant sequence (repeating the same value indefinitely).
    """

    def __init__(self, value):
        super().__init__()
        self.value = value

    def __repr__(self):
        return f"<Constant: {self.value!r}>"

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

    def __repr__(self):
        return f"<Boolean: p={self.p!r}>"

    def reset(self, seed):
        # super().reset(seed)
        self.randgen.seed(seed)
        return self

    def __next__(self):
        return self.randgen.random() < self.p


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

    def __repr__(self):
        return f"<Integer: low={self.low!r}, high={self.high!r}>"

    def reset(self, seed):
        self.randgen.seed(seed)
        return self

    def __next__(self):
        return self.randgen.randint(self.low, self.high)


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

    def __repr__(self):
        return f"<HashDigest: length={self.length!r}, as_bytes={self.as_bytes!r}, lowercase={self.lowercase!r}>"

    def reset(self, seed):
        self.randgen.seed(seed)
        return self

    def __next__(self):
        val = self.randgen.bytes(self._internal_length)
        return self._maybe_convert_to_uppercase(self._maybe_convert_to_hex(val))


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

    def __repr__(self):
        return f"<FakerGenerator: method={self.method!r}, locale={self.locale!r}, faker_args={self.faker_args!r}>"

    def reset(self, seed):
        # super().reset(seed)
        self.fake.seed_instance(seed)
        return self

    def __next__(self):
        return self.randgen(**self.faker_args)
