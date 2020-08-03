from random import Random


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

    def _set_state_from(self, other):
        self.randgen.setstate(other.randgen.getstate())
