import warnings

from .base import TohuBaseGenerator


def find_tohu_generators(x):
    """
    Find any attributes of the instance `x` or its class which are tohu generators.
    """
    class_candidates = list(x.__class__.__dict__.items())
    instance_candidates = list(x.__dict__.items())
    candidates = class_candidates + instance_candidates
    return {name: gen for (name, gen) in candidates if isinstance(gen, TohuBaseGenerator)}


class CustomGenerator(TohuBaseGenerator):
    """
    CustomGenerator allows combining other generators into a single entity.
    """

    def __init__(self):
        super().__init__()
        self._tohu_generators = find_tohu_generators(self)

    def __next__(self):
        warnings.warn("TODO: return items as TohuItemS rather than dicts!")
        return {name: next(g) for (name, g) in self._tohu_generators.items()}

    def reset(self, seed=None):
        warnings.warn("FIXME: implement reset() properly!")
        return self
