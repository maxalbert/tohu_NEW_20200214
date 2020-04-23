from .base import is_tohu_generator, SeedGenerator
from .looping_NEW import LoopRunnerNEW, is_loop_variable
from .tohu_items_class import make_tohu_items_class

__all__ = ["TohuNamespaceNEW2"]


class NonExistentTohuItemsClassError(Exception):
    pass


class NonExistentTohuItemsClass:
    def __repr__(self):
        return "<NonExistentTohuItemsClass>"

    def __call__(self, *args, **kwargs):
        raise NonExistentTohuItemsClassError(
            "Please call `set_tohu_items_class()` on the tohu namespace before generating items."
        )


class TohuNamespaceNEW2:
    def __init__(self):
        self.seed_generator = SeedGenerator()
        self.tohu_items_cls = NonExistentTohuItemsClass()

        self.field_generators = {}
        self.all_generators = {}
        self.generators_to_reset = []

        # When a field generator is added to the tohu namespace, internally we
        # create and store a spawn (or clone). The `gen_mapping` attribute keeps
        # track of the mapping between original -> spawned/cloned generators
        # so that we can rewire dependencies correctly when a derived generator
        # is added to the tohu namespace.
        self.gen_mapping = {}

    def add_field_generators_from_dict(self, dct):
        for name, g in dct.items():
            if is_tohu_generator(g):
                self.add_field_generator(name, g)

    def add_field_generator(self, name, g):
        g_internal = g.spawn(gen_mapping=self.gen_mapping)
        self.field_generators[name] = g_internal
        self.all_generators[name] = g_internal
        self.gen_mapping[g] = g_internal
        self.generators_to_reset.append(g_internal)

    def add_non_field_generator(self, name, g, is_externally_managed):
        if not is_externally_managed:
            # Presumably all we have to do in this case is to add
            # g_internal to the list `self.generators_to_reset`?
            raise NotImplementedError(
                "TODO: Add support for non-field generators that are internally managed by the tohu namespace. "
                "This is likely a valid use case but not currently supported."
            )

        g_internal = g.clone()
        self.all_generators[name] = g_internal
        self.gen_mapping[g] = g_internal

    def extract_loop_runner(self):
        loop_runner = LoopRunnerNEW()
        for _, x in self.all_generators.items():
            if is_loop_variable(x):
                loop_runner.add_loop_variable(x, x.loop_level)
        return loop_runner

    def set_tohu_items_class(self, name):
        field_names = list(self.field_generators.keys())
        self.tohu_items_cls = make_tohu_items_class(name, field_names=field_names)

    def reset(self, seed):
        self.seed_generator.reset(seed)

        for g in self.generators_to_reset:
            g.reset(next(self.seed_generator))

    def __next__(self):
        return self.tohu_items_cls(*(next(g) for g in self.field_generators.values()))
