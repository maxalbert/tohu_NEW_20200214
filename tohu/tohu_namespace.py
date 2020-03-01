from .base import SeedGenerator
from .derived_generators import Apply
from .logging import logger
from .looping import LoopVariable
from .utils import identity
from .tohu_items_class import make_tohu_items_class


class TohuNamespaceError(Exception):
    """ Custom exception """


class NonExistentTohuItemsClass:
    # This is a placeholder for a proper TohuItemsClass, which will be
    # created when `TohuNamespace.make_tohu_items_class()` is called.
    # This only exists to produce a meaningful error message in case
    # make_tohu_items_class() isn't called before trying to have the
    # TohuNamespace instance generate items.

    def __call__(self):
        raise TohuNamespaceError(
            f"TODO: tohu items class needs to be created before the tohu namespace can generate elements."
        )


class TohuNamespace:
    def __init__(self, tohu_items_class_name):
        self.tohu_items_class_name = tohu_items_class_name
        self.tohu_items_class = NonExistentTohuItemsClass()
        self.seed_generator = SeedGenerator()
        self.gen_mapping = {}
        self.hidden_generators = {}
        self.generators = {}

    @property
    def _all_generators(self):
        res = self.hidden_generators.copy()
        res.update(self.generators)
        return res

    def add_generator(self, name, gen):
        if gen in self.gen_mapping:
            gen = Apply(identity, gen)
        gen_spawned = gen.spawn(self.gen_mapping)
        self.gen_mapping[gen] = gen_spawned
        if gen.is_hidden:
            self.hidden_generators[name] = gen_spawned
        else:
            self.generators[name] = gen_spawned

    def make_tohu_items_class(self):
        field_names = list(self.generators.keys())
        self.tohu_items_class = make_tohu_items_class(self.tohu_items_class_name, field_names)

    def __next__(self):
        gen_vals = (next(g) for g in self.generators.values())
        return self.tohu_items_class(*gen_vals)

    def reset(self, seed):
        self.seed_generator.reset(seed)

        logger.debug(f"In TohuNamespace for items class '{self.tohu_items_class_name}':")
        for name, g in self._all_generators.items():
            next_seed = next(self.seed_generator)
            logger.debug(f"  - Resetting {name}={g} with seed={next_seed}")
            g.reset(next_seed)

    @property
    def loop_variables(self):
        return [g for g in self._all_generators.values() if isinstance(g, LoopVariable)]

    def advance_loop_variables(self):
        for g in self.loop_variables:
            g.advance()
