from .base import SeedGenerator


__all__ = ["TohuNamespaceNEW3"]


class TohuNamespaceNEW3:
    def __init__(self, dependency_mapping=None):
        self.dependency_mapping = dependency_mapping or {}
        self.generators = {}
        self.seed_generator = SeedGenerator()

    def __format__(self, format_specifier):
        s = f"<{self.__class__.__name__}\n"
        for name, g in self.generators.items():
            s += f"   {name!r}: {g:debug}\n"
        s += f">"
        return s

    def add_spawn_of(self, g, *, name):
        g_spawned = g.spawn(self.dependency_mapping)
        self.dependency_mapping[g] = g_spawned
        self.generators[name] = g_spawned

    def reset(self, seed):
        self.seed_generator.reset(seed)

        for g in self.generators.values():
            g.reset(next(self.seed_generator))

    def __next__(self):
        return tuple(next(g) for g in self.generators.values())
