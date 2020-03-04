import inspect

from .base import TohuBaseGenerator
from .custom_generator import CustomGenerator
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

        yield from self.custom_gen_instance._tohu_namespace.loop_runner.run_loop_to_generate_items_with(
            self.custom_gen_instance, num_iterations
        )

    def generate_as_list(self, *, num_iterations, seed):
        return list(self.generate_as_stream(num_iterations=num_iterations, seed=seed))


class ForeachGeneratorClass:
    def __init__(self, custom_gen_cls, loop_level):
        self.custom_gen_cls = custom_gen_cls
        self.loop_level = loop_level

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

        if inspect.isclass(cls) and issubclass(cls, CustomGenerator):
            custom_gen_cls = cls
            loop_level = 1
        else:
            assert isinstance(cls, ForeachGeneratorClass)
            custom_gen_cls = cls.custom_gen_cls
            loop_level = cls.loop_level + 1

        for x in loop_vars.values():
            x.loop_level = loop_level

        stored_gens = {name: x for (name, x) in custom_gen_cls.__dict__.items() if isinstance(x, TohuBaseGenerator)}
        for name in stored_gens.keys():
            delattr(custom_gen_cls, name)
        for name, x in loop_vars.items():
            setattr(custom_gen_cls, name, x)
        for name, g in stored_gens.items():
            setattr(custom_gen_cls, name, g)

        return ForeachGeneratorClass(custom_gen_cls, loop_level)

    return wrapper
