from .base import SeedGenerator
from .derived_generators import Apply
from .logging import logger
from .utils import identity
from .tohu_items_class import make_tohu_items_class


class TohuNamespaceError(Exception):
    """ Custom exception """


class NonExistentTohuItemsClass:
    def __call__(self):
        raise TohuNamespaceError(
            f"TODO: tohu items class needs to be created before the tohu namespace can generate elements."
        )


class TohuNamespace:
    def __init__(self, tohu_items_class_name):
        self.generators = {}
        self.tohu_items_class_name = tohu_items_class_name
        self.tohu_items_class = NonExistentTohuItemsClass()
        self.seed_generator = SeedGenerator()
        self.gen_mapping = {}

    def add_generator(self, name, gen):
        if gen in self.generators.values():
            gen = Apply(identity, gen)
        gen_spawned = gen.spawn(self.gen_mapping)
        self.generators[name] = gen_spawned
        self.gen_mapping[gen] = gen_spawned

    def make_tohu_items_class(self):
        field_names = list(self.generators.keys())
        self.tohu_items_class = make_tohu_items_class(self.tohu_items_class_name, field_names)

    def __next__(self):
        gen_vals = (next(g) for g in self.generators.values())
        return self.tohu_items_class(*gen_vals)

    def reset(self, seed):
        self.seed_generator.reset(seed)

        logger.debug(f"In TohuNamespace for items class '{self.tohu_items_class_name}':")
        for name, g in self.generators.items():
            next_seed = next(self.seed_generator)
            logger.debug(f"  - Resetting {name}={g} with seed={next_seed}")
            g.reset(next_seed)
