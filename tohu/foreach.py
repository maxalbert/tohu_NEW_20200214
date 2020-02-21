import inspect

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
        # TODO: add check that the list `nums` has at least as many values as were given for each of the loop variables!

        self.cgen_instance.reset(seed)

        for N in nums:
            # TODO: reset the generator within each loop instead of only once at the beginning?
            yield from self.cgen_instance.generate_as_stream(N)
            try:
                self.cgen_instance.advance_loop_variables()
            except IndexError:
                break


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
        return ForeachGeneratorClass(cls)

    return wrapper
