import warnings

from .base import TohuBaseGenerator, SeedGenerator
from .tohu_items_class import make_tohu_items_class, derive_tohu_items_class_name


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
        self.seed_generator = SeedGenerator()
        self._tohu_generators = find_tohu_generators(self)

        tohu_items_class_name = derive_tohu_items_class_name(self.__class__.__name__)
        self._tohu_items_class = make_tohu_items_class(tohu_items_class_name, self._tohu_generators.keys())

    def __next__(self):
        return self._tohu_items_class(*(next(g) for g in self._tohu_generators.values()))

    def reset(self, seed=None):
        # First reset the internal seed generator
        self.seed_generator.reset(seed)

        # Then reset each constituent generator using
        # a fresh seed produced by the seed generator.
        for _, g in self._tohu_generators.items():
            g.reset(next(self.seed_generator))

        return self
