import inspect

from .base import TohuBaseGenerator
from .looping import LoopVariable

__all__ = ["foreach"]


def restore_globals(global_vars, names, clashes):

    for name in names:
        if name in clashes:
            # restore items that were previously defined
            global_vars[name] = clashes[name]
        else:
            # remove items which didn't exist before
            global_vars.pop(name)


class ForeachGeneratorInstance:
    def __init__(self, cgen_instance):
        self.cgen_instance = cgen_instance

    def __repr__(self):
        return f"<@foreach-wrapped {self.cgen_instance} >"

    def generate_as_stream(self, *, nums, seed):
        if seed is not None:
            self.cgen_instance.reset(seed)

        for N in nums:
            # TODO: reset the generator within each loop instead of only once at the beginning?
            yield from self.cgen_instance.generate_as_stream(N)
            try:
                self.cgen_instance.advance_loop_variables()
            except IndexError:
                break

    def generate_as_list(self, *, nums, seed):
        return list(self.generate_as_stream(nums=nums, seed=seed))


class ForeachGeneratorClass:
    def __init__(self, cgen_cls):
        self.cgen_cls = cgen_cls

    def __call__(self, *args, **kwargs):
        cgen_instance = self.cgen_cls(*args, **kwargs)
        return ForeachGeneratorInstance(cgen_instance)


def foreach(**var_defs):
    new_names = var_defs.keys()
    parent_frame = inspect.currentframe().f_back
    global_vars = parent_frame.f_globals

    clashes = {name: global_vars[name] for name in new_names if name in global_vars}
    loop_vars = {name: LoopVariable(name, values) for name, values in var_defs.items()}
    global_vars.update(loop_vars)

    def wrapper(cls):
        restore_globals(global_vars, new_names, clashes)

        stored_gens = {name: x for (name, x) in cls.__dict__.items() if isinstance(x, TohuBaseGenerator)}
        for name in stored_gens.keys():
            delattr(cls, name)
        for name, x in loop_vars.items():
            setattr(cls, name, x)
        for name, g in stored_gens.items():
            setattr(cls, name, g)

        return ForeachGeneratorClass(cls)

    return wrapper
