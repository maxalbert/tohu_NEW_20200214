from .base import SeedGenerator, is_tohu_generator


__all__ = ["TohuNamespaceNEW3"]


class TohuNamespaceNEW3:
    def __init__(self, dependency_mapping=None):
        self.dependency_mapping = dependency_mapping or {}
        self.field_generators = {}
        self.seed_generator = SeedGenerator()

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
        g_spawned = g.spawn(self.dependency_mapping)
        self.dependency_mapping[g] = g_spawned
        self.field_generators[name] = g_spawned

    def reset(self, seed):
        self.seed_generator.reset(seed)

        for g in self.field_generators.values():
            g.reset(next(self.seed_generator))

    def __next__(self):
        return tuple(next(g) for g in self.field_generators.values())
