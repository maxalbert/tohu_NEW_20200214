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

    def __format__(self, format_specifier):
        if format_specifier == "debug":
            clsname = self.__class__.__name__
            name = "" if self.tohu_name is None else f"{self.tohu_name}: "
            arg_gens_descr = ", ".join(["{:debug}".format(g) for g in self.arg_gens])
            kwarg_gens_descr = ", ".join(["{}: {:debug}".format(name, g) for (name, g) in self.kwarg_gens.items()])
            return (
                f"<{name}{clsname} (id={self.tohu_id})\n"
                f"   arg_gens=[{arg_gens_descr}]\n"
                f"   kwarg_gens={{{kwarg_gens_descr}}}]\n"
                ">"
            )
        else:
            return repr(self)

    def __next__(self):
        args = [next(g) for g in self.arg_gens]
        kwargs = {name: next(g) for name, g in self.kwarg_gens.items()}
        return self.func(*args, **kwargs)

    def reset(self, seed):
        super().reset(seed)

    def spawn(self, gen_mapping=None):
        if gen_mapping is None:
            # This code path is reached during cloning, because we don't require a `gen_mapping` argument in `clone()`.
            new_arg_gens = self.arg_gens
            new_kwarg_gens = self.kwarg_gens
        else:
            try:
                new_arg_gens = [gen_mapping[g.parent] for g in self.arg_gens]
                new_kwarg_gens = {name: gen_mapping[g.parent] for name, g in self.kwarg_gens.items()}
            except KeyError:
                raise ValueError("Generator mapping does not contain a value for some generator!")

        new_gen = Apply(self.func, *new_arg_gens, **new_kwarg_gens)
        new_gen._set_state_from(self)
        return new_gen

    def _set_state_from(self, other):
        super()._set_state_from(other)
        for g1, g2 in zip(self.arg_gens, other.arg_gens):
            g1._set_state_from(g2)
        for g1, g2 in zip(self.kwarg_gens.values(), other.kwarg_gens.values()):
            g1._set_state_from(g2)
