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
    def __repr__(self):
        return "<NonExistentTohuItemsClass>"

    def __call__(self, *args, **kwargs):
        raise NonExistentTohuItemsClassError(
            "Please call `set_tohu_items_class()` on the tohu namespace before generating items."
        )


class TohuNamespaceNEW:
    def __init__(self):
        self.field_generators = {}
        self.all_generators = {}
        self.generators_to_reset = []
        self.loop_variables = []
        self.spawn_mapping = {}
        self.seed_generator = SeedGenerator()
        self.tohu_items_cls = NonExistentTohuItemsClass()

    def add_field_generators_from_dict(self, dct):
        for name, g in dct.items():
            if is_tohu_generator(g):
                self.add_field_generator(name, g)

    def add_loop_variables_from_dict(self, dct):
        for name, g in dct.items():
            if is_loop_variable(g):
                self.add_loop_variable_as_hidden_non_field_generator(name, g)

    def add_field_generator(self, name, g):
        if g not in self.spawn_mapping:
            g_internal = g.spawn(gen_mapping=self.spawn_mapping)
            self.spawn_mapping[g] = g_internal
            self.generators_to_reset.append(g_internal)
        else:
            # This generator has been added before, so we just need
            # to clone it and register the clone under the new name.
            g_internal = self.spawn_mapping[g].clone()

        self.all_generators[name] = g_internal
        self.field_generators[name] = g_internal

    def add_loop_variable_as_hidden_non_field_generator(self, name, g):
        # TODO: for consistency, should we just use the first part of `add_field_generator()` above
        #       and simply avoid adding `g` to the field_generators dictionary?
        assert is_loop_variable(g)
        g_internal = g.clone()
        self.spawn_mapping[g] = g_internal
        self.all_generators[name] = g_internal
        self.loop_variables.append(g_internal)

    # def extract_loop_runner(self):
    #     loop_runner = LoopRunnerNEW()
    #     for name, x in self.generators.items():
    #         loop_runner.add_loop_variable(x, x.loop_level)
    #     return loop_runner

    def set_tohu_items_class(self, name):
        field_names = list(self.field_generators.keys())
        self.tohu_items_cls = make_tohu_items_class(name, field_names=field_names)

    def reset(self, seed):
        self.seed_generator.reset(seed)

        for g in self.generators_to_reset:
            g.reset(next(self.seed_generator))

        for g in self.loop_variables:
            g.reset_loop_variable()

    def __next__(self):
        return self.tohu_items_cls(*(next(g) for g in self.field_generators.values()))
