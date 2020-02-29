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
    def __init__(self, custom_gen_instance):
        self.custom_gen_instance = custom_gen_instance

    def __repr__(self):
        return f"<@foreach-wrapped {self.custom_gen_instance} >"

    def generate_as_stream(self, *, num_iterations, seed=None):
        if seed is not None:
            self.custom_gen_instance.reset(seed)

        for N in num_iterations:
            # TODO: reset the generator within each loop instead of only once at the beginning?
            yield from self.custom_gen_instance.generate_as_stream(N)
            try:
                self.custom_gen_instance.advance_loop_variables()
            except IndexError:
                break

    def generate_as_list(self, *, num_iterations, seed):
        return list(self.generate_as_stream(num_iterations=num_iterations, seed=seed))


class ForeachGeneratorClass:
    def __init__(self, custom_gen_cls):
        self.custom_gen_cls = custom_gen_cls

    def __call__(self, *args, **kwargs):
        custom_gen_instance = self.custom_gen_cls(*args, **kwargs)
        return ForeachGeneratorInstance(custom_gen_instance)


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
