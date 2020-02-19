from .base import TohuBaseGenerator

__all__ = ["Apply"]


class Apply(TohuBaseGenerator):
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        assert all([isinstance(g, TohuBaseGenerator) for g in args])
        assert all([isinstance(g, TohuBaseGenerator) for g in kwargs.values()])
        self.func = func
        self.arg_gens = [g.clone() for g in args]
        self.kwarg_gens = {name: g.clone() for name, g in kwargs.items()}

    def __next__(self):
        args = [next(g) for g in self.arg_gens]
        kwargs = {name: next(g) for name, g in self.kwarg_gens.items()}
        return self.func(*args, **kwargs)

    def reset(self, seed):
        super().reset(seed)

    def spawn(self):
        new_gen = Apply(self.func, *self.arg_gens, **self.kwarg_gens)
        new_gen._set_state_from(self)
        return new_gen

    def _set_state_from(self, other):
        for g1, g2 in zip(self.arg_gens, other.arg_gens):
            g1._set_state_from(g2)
        for g1, g2 in zip(self.kwarg_gens.values(), other.kwarg_gens.values()):
            g1._set_state_from(g2)
