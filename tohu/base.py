import hashlib

from itertools import islice
from random import Random
from tqdm import tqdm


class SeedGenerator:
    """
    This class is used in custom generators to create a collection of
    seeds when reset() is called, so that each of the constituent
    generators can be re-initialised with a different seed in a
    reproducible way.

    This is almost identical to the `tohu.Integer` generator, but we
    need a version which does *not* inherit from `TohuBaseGenerator`,
    to avoid confusion in the code which generates the TohuItem class
    for custom generators.
    """

    def __init__(self):
        self.randgen = Random()
        self.minval = 0
        self.maxval = 2 ** 32 - 1

    def reset(self, seed):
        self.randgen.seed(seed)
        return self

    def __next__(self):
        return self.randgen.randint(self.minval, self.maxval)


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

    def __iter__(self):
        return self

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

    def generate_as_stream(self, num, *, seed, progressbar=False):
        """
        Return sequence of `num` elements.

        If `seed` is not None, the generator is reset
        using this seed before generating the elements.
        """
        self.reset(seed)

        items = islice(self, num)
        if progressbar:  # pragma: no cover
            items = tqdm(items, total=num)

        yield from items

    def generate_as_list(self, num, *, seed, progressbar=False):
        return list(self.generate_as_stream(num, seed=seed, progressbar=progressbar))
