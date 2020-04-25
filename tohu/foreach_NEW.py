import inspect
from .custom_generator_NEW import CustomGeneratorNEW
from .looping_NEW import LoopVariableNEW


def restore_globals(global_vars, names, clashes):

    for name in names:
        if name in clashes:
            # restore items that were previously defined
            global_vars[name] = clashes[name]
        else:
            # remove items which didn't exist before
            global_vars.pop(name)


class ForeachGeneratorInstance:
    def __init__(self, custom_gen_instance: CustomGeneratorNEW):
        self.custom_gen_instance = custom_gen_instance

    def __repr__(self):
        return f"<Looped custom generator instance: {self.custom_gen_instance!r}, wrapped using @foreach>"

    def generate_as_stream(self, *, num_iterations, seed=None):
        # FIXME: Demeter violation!
        yield from self.custom_gen_instance._loop_runner.iter_loop_var_combinations_with_generator(
            self.custom_gen_instance, num_iterations, seed=seed
        )


class ForeachGeneratorClass:
    def __init__(self, custom_gen_cls):
        self.custom_gen_cls = custom_gen_cls

    def __repr__(self):
        return f"<Looped custom generator class: {self.custom_gen_cls.__name__!r}, wrapped using @foreach>"

    def __call__(self, *args, **kwargs):
        custom_gen_instance = self.custom_gen_cls(*args, **kwargs)
        return ForeachGeneratorInstance(custom_gen_instance)


def foreach_NEW(**var_defs):
    new_names = var_defs.keys()
    parent_frame = inspect.currentframe().f_back
    global_vars = parent_frame.f_globals

    clashes = {name: global_vars[name] for name in new_names if name in global_vars}
    loop_vars = {name: LoopVariableNEW(name, values) for name, values in var_defs.items()}
    global_vars.update(loop_vars)

    def wrapper(cls):
        restore_globals(global_vars, new_names, clashes)

        this_loop_level = cls._tohu_loop_level + 1

        cls._tohu_loop_level = this_loop_level
        for x in loop_vars.values():
            x.set_loop_level(this_loop_level)
            cls._tohu_cg_class_loop_variables.append(x)

        return ForeachGeneratorClass(cls)

    return wrapper
