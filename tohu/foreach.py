import inspect

from .logging import logger

__all__ = ["foreach"]


def restore_globals(global_vars, names, clashes):

    for name in names:
        if name in clashes:
            # restore items that were previously defined
            global_vars[name] = clashes[name]
        else:
            # remove items which didn't exist before
            global_vars.pop(name)


def foreach(**var_defs):
    new_names = var_defs.keys()
    parent_frame = inspect.currentframe().f_back
    global_vars = parent_frame.f_globals
    # local_vars = parent_frame.f_locals

    clashes = {name: global_vars[name] for name in new_names if name in global_vars}
    loop_vars = {name: values for name, values in var_defs.items()}
    global_vars.update(loop_vars)

    # global_vars.update(var_defs)

    def wrapper(cls):
        logger.debug(f"In @foreach decorator: wrapping {cls}")
        restore_globals(global_vars, new_names, clashes)
        return cls

    return wrapper
