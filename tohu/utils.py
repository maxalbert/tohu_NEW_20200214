__all__ = ["print_generated_sequence", "identity"]


def print_generated_sequence(gen, num, *, seed, sep=", ", fmt=""):
    """
    Helper function which prints a sequence of `num` item produced by the random generator `gen`.

    Examples
    --------
    >>> g = Integer(1, 20)
    >>> print_generated_sequence(g, num=10, seed=99999, fmt='02d', sep=", ")
    Generated sequence: 06, 07, 18, 12, 19, 05, 17, 15, 09, 18
    """
    gen.reset(seed)

    elems = [format(next(gen), fmt) for _ in range(num)]
    sep_initial = "\n\n" if "\n" in sep else " "
    print("Generated sequence:{}{}".format(sep_initial, sep.join(elems)))


def identity(x):
    """
    Helper function which returns its argument unchanged.
    That is, `identity(x)` returns `x` for any input `x`.
    """
    return x
