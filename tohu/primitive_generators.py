from random import Random

__all__ = ["Constant", "Integer"]


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
