from tohu.base import is_tohu_generator
from tohu.seed_generator import SeedGenerator
from tohu.tohu_items_class import make_tohu_items_class

__all__ = ["TohuNamespaceNEW3"]


class NonExistentTohuItemsClassError(Exception):
    """
    Custom exception to indicate that `set_tohu_items_class()` has not been called.
    """


class NonExistentTohuItemsClass:
    # This is a placeholder for a proper TohuItemsClass, which will be
    # created when `TohuNamespace.make_tohu_items_class()` is called.
    # This only exists to produce a meaningful error message in case
    # make_tohu_items_class() isn't called before trying to generate
    # tohu items using the TohuNamespace instance.

    def __repr__(self):
        return "<NonExistentTohuItemsClass>"

    def __call__(self, *args, **kwargs):
        raise NonExistentTohuItemsClassError(
            "Please call `set_tohu_items_class()` on the tohu namespace before generating items."
        )


class TohuNamespaceNEW3:
    def __init__(self, dependency_mapping=None):
        self.dependency_mapping = dependency_mapping or {}
        self.field_generators = {}
        self.seed_generator = SeedGenerator()
        self.tohu_items_cls = NonExistentTohuItemsClass()

    def __format__(self, format_specifier):
        s = f"<{self.__class__.__name__}\n"
        for name, g in self.field_generators.items():
            s += f"   {name!r}: {g:debug}\n"
        s += f">"
        return s

    @property
    def field_names(self):
        return tuple(self.field_generators.keys())

    def add_field_generators_from_dict(self, dct):
        for name, g in dct.items():
            if is_tohu_generator(g):
                self.add_field_generator(g, name=name)

    def add_field_generator(self, g, *, name):
        if g not in self.dependency_mapping:
            g_spawned = g.spawn(self.dependency_mapping)
            self.dependency_mapping[g] = g_spawned
            self.field_generators[name] = g_spawned
        else:
            # This generator has been added before, so we just need
            # to clone it and register the clone under the new name.
            self.field_generators[name] = self.dependency_mapping[g].clone()

    # TODO: only added temporarily
    def set_tohu_items_class(self, name):
        field_names = list(self.field_generators.keys())
        self.tohu_items_cls = make_tohu_items_class(name, field_names=field_names)

    def reset(self, seed):
        self.seed_generator.reset(seed)

        for g in self.field_generators.values():
            g.reset(next(self.seed_generator))

    def __next__(self):
        # return tuple(next(g) for g in self.field_generators.values())
        return self.tohu_items_cls(*(next(g) for g in self.field_generators.values()))
