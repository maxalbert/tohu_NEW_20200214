from typing import Callable, Sequence


class LoopVariable:
    def __init__(self, name, values):
        self.name = name
        self.values = values
        self.loop_level = None

    def __repr__(self):
        return f"<LoopVariable: name={self.name!r}, values={self.values!r}>"

    def set_loop_level(self, loop_level):
        self.loop_level = loop_level
        return self


class NumIterationsGetterFromCallable:
    def __init__(self, func_num_iterations):
        self.func_num_iterations = func_num_iterations

    def __call__(self, **kwargs):
        return self.func_num_iterations(**kwargs)


class NumIterationsGetterFromInt:
    def __init__(self, num_iterations):
        self.num_iterations = num_iterations

    def __call__(self, **kwargs):
        return self.num_iterations


class NumIterationsGetterFromSequence:
    def __init__(self, seq_num_iterations):
        self.seq_num_iterations = seq_num_iterations
        self.idx = -1

    def __call__(self, **kwargs):
        self.idx += 1
        try:
            return self.seq_num_iterations[self.idx]
        except IndexError:
            raise StopIteration


def make_num_iterations_getter(num_iterations):
    if isinstance(num_iterations, Callable):
        return NumIterationsGetterFromCallable(num_iterations)
    elif isinstance(num_iterations, int):
        return NumIterationsGetterFromInt(num_iterations)
    elif isinstance(num_iterations, Sequence):
        return NumIterationsGetterFromSequence(num_iterations)
    else:
        raise TypeError("Invalid type for argument `num_iterations`. Must be one of: integer, sequence, callable")


class LoopRunner:
    def __init__(self, loop_variables):
        self.loop_variables = loop_variables
        self.max_level = max([x.loop_level for x in self.loop_variables.values()])

    def get_loop_variables_at_level(self, loop_level):
        return {name: x for name, x in self.loop_variables.items() if x.loop_level == loop_level}

    def run_loop_iterations_with(self, f_do_stuff):
        return self._run_loop_iterations_impl(f_do_stuff, self.max_level)

    def _run_loop_iterations_impl(self, f_do_stuff, cur_loop_level, **loop_var_values_at_higher_levels):
        if cur_loop_level == 0:
            yield from f_do_stuff(**loop_var_values_at_higher_levels)
        else:
            for cur_vals in self.iter_loop_var_values_at_level(cur_loop_level):
                yield from self._run_loop_iterations_impl(
                    f_do_stuff, cur_loop_level=cur_loop_level - 1, **cur_vals, **loop_var_values_at_higher_levels
                )

    def iter_loop_var_values_at_level(self, loop_level):
        loop_vars_at_level = self.get_loop_variables_at_level(loop_level)
        var_names = list(loop_vars_at_level)
        all_var_values = zip(*(x.values for x in loop_vars_at_level.values()))
        for vals in all_var_values:
            yield dict(zip(var_names, vals))

    def get_loop_iteration_lengths(self, num_iterations):
        get_num_iterations = make_num_iterations_getter(num_iterations)

        def f_do_stuff(**kwargs):
            yield (kwargs, get_num_iterations(**kwargs))

        return self.run_loop_iterations_with(f_do_stuff)
