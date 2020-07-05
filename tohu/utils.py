from ._version import get_versions

__all__ = ["print_generated_sequence", "identity", "as_list", "print_tohu_version"]


def print_generated_sequence(gen, num, *, seed=None, sep=", ", fmt="{}"):
    """
    Helper function which prints a sequence of `num` item produced by the random generator `gen`.

    Examples
    --------
    >>> g = Integer(1, 20)
    >>> print_generated_sequence(g, num=10, seed=99999, fmt='{:02d}', sep=", ")
    Generated sequence: 06, 07, 18, 12, 19, 05, 17, 15, 09, 18
    """
    if seed is not None:
        gen.reset(seed)

    elems = [fmt.format(next(gen)) for _ in range(num)]
    sep_initial = "\n\n" if "\n" in sep else " "
    print("Generated sequence:{}{}".format(sep_initial, sep.join(elems)))


def identity(x):
    """
    Helper function which returns its argument unchanged.
    That is, `identity(x)` returns `x` for any input `x`.
    """
    return x


def as_list(seq):
    """
    Helper function which converts the input sequence to a list
    (returns the input value unchanged if it is already a list).
    """
    if isinstance(seq, list):
        return seq
    else:
        return list(seq)


def print_tohu_version():
    """
    Helper function to print the current tohu version (for convenience during prototyping and debugging).
    """
    tohu_version = get_versions()["version"]
    print(f"Tohu version: {tohu_version}")
