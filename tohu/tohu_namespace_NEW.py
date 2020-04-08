from .base import SeedGenerator, TohuBaseGenerator
from .looping_NEW import LoopRunnerNEW, LoopVariableNEW
from .tohu_items_class import make_tohu_items_class

__all__ = ["TohuNamespaceNEW"]


def is_tohu_generator(g):
    return isinstance(g, TohuBaseGenerator)


def is_loop_variable(g):
    return isinstance(g, LoopVariableNEW)


class NonExistentTohuItemsClassError(Exception):
    pass


class NonExistentTohuItemsClass:
    def __call__(self, *args, **kwargs):
        raise NonExistentTohuItemsClassError(
            "Please call `set_tohu_items_class()` on the tohu namespace before generating items."
        )


class TohuNamespaceNEW:
    def __init__(self):
        self.generators = {}
        self.generators_to_reset = []
        self.spawn_mapping = {}
        self.seed_generator = SeedGenerator()
        self.tohu_items_cls = NonExistentTohuItemsClass()

    def add_tohu_generators_from_dict(self, dct):
        for name, g in dct.items():
            if is_tohu_generator(g):
                self.add_generator(name, g)

    def add_generator(self, name, g):
        if g not in self.spawn_mapping:
            if not is_loop_variable(g):
                g_internal = g.spawn(gen_mapping=self.spawn_mapping)
            else:
                g_internal = g.clone()

            self.spawn_mapping[g] = g_internal
            self.generators_to_reset.append(g_internal)
        else:
            # This generator has been added before, so we just
            # need to register it under a new name.
            g_internal = self.spawn_mapping[g].clone()

        self.generators[name] = g_internal

    # def extract_loop_runner(self):
    #     loop_runner = LoopRunnerNEW()
    #     for name, x in self.generators.items():
    #         loop_runner.add_loop_variable(x, x.loop_level)
    #     return loop_runner
    #
    # def add_loop_variable(self, g):
    #     g_internal = g.clone()
    #     self.spawn_mapping[g] = g_internal
    #
    # def set_tohu_items_class(self, tohu_items_class_name):
    #     self.tohu_items_cls = make_tohu_items_class(tohu_items_class_name, field_names=self.generators.keys())
    #
    # def reset(self, seed):
    #     self.seed_generator.reset(seed)
    #     # for _, g in self.generators.items():
    #     for g in self.generators_to_reset:
    #         g.reset(next(self.seed_generator))
    #
    # def __next__(self):
    #     return self.tohu_items_cls(*(next(g) for g in self.generators.values()))
