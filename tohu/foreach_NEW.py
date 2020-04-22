import inspect
from .looping_NEW import LoopVariableNEW


def restore_globals(global_vars, names, clashes):

    for name in names:
        if name in clashes:
            # restore items that were previously defined
            global_vars[name] = clashes[name]
        else:
            # remove items which didn't exist before
            global_vars.pop(name)


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

        return cls

    return wrapper
