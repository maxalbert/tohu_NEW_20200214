import inspect
from .logging import logger
from .looped_custom_generator import LoopedCustomGeneratorClass
from .looping_NEW_3 import LoopVariableNEW3


def declare_loop_variables_in_stack_frame(var_defs, stack_frame):
    logger.debug(f"Declaring the following loop variables ({stack_frame!r}): {var_defs}")
    new_names = var_defs.keys()
    global_vars = stack_frame.f_globals

    clashes = {name: global_vars[name] for name in new_names if name in global_vars}
    loop_vars = {name: LoopVariableNEW3(name, values) for name, values in var_defs.items()}
    global_vars.update(loop_vars)

    return loop_vars, clashes


def foreach_NEW3(**loop_var_declarations):
    parent_frame = inspect.currentframe().f_back
    loop_vars, clashes = declare_loop_variables_in_stack_frame(loop_var_declarations, parent_frame)

    def wrap_custom_generator_class(cls):
        logger.debug(f"Wrapping custom generator class: {cls}")
        wrapped_cls = LoopedCustomGeneratorClass(cls)
        wrapped_cls.add_loop_variables_at_next_level_up(loop_vars)
        return wrapped_cls

    return wrap_custom_generator_class
