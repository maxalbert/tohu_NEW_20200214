def print_generated_sequence(gen, num, *, sep=", ", fmt="", seed=None):
    """
    Helper function which prints a sequence of `num` item produced by the random generator `gen`.

    Example:
    >>> g = Integer(1, 20)
    >>> print_generated_sequence(g, num=10, seed=99999, fmt='02d', sep=", ")
    Generated sequence: 06, 07, 18, 12, 19, 05, 17, 15, 09, 18
    """
    if seed:
        gen.reset(seed)

    elems = [format(next(gen), fmt) for _ in range(num)]
    sep_initial = "\n\n" if "\n" in sep else " "
    print("Generated sequence:{}{}".format(sep_initial, sep.join(elems)))
