from itertools import groupby
from typing import Callable, Sequence

from .base import TohuBaseGenerator


class LoopVariable(TohuBaseGenerator):
    def __init__(self, name, values):
        super().__init__()
        self.name = name
        self.values = list(values)
        self.loop_level = None
        self.is_hidden = True
        self.idx = 0
        self.cur_value = self.values[0]

    def __next__(self):
        return self.cur_value

    def __repr__(self):
        return f"<LoopVariable: name={self.name!r}, loop_level={self.loop_level!r}, values={self.values!r}, cur_value={self.cur_value!r}>"

    def advance(self):
        self.idx += 1
        try:
            self.cur_value = self.values[self.idx]
        except IndexError:
            raise StopIteration(f"Loop variable has been exhausted: {self}")

        for c in self.clones:
            c.advance()

    def reset_loop_variable(self):
        self.idx = 0
        self.cur_value = self.values[0]

    def set_loop_level(self, loop_level):
        self.loop_level = loop_level
        return self

    def spawn(self, gen_mapping=None):
        return LoopVariable(self.name, self.values).set_loop_level(self.loop_level)


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


class NumIterationsSequenceExhausted(Exception):
    """
    Custom exception to indicate that a `num_iterations` sequence has been exhausted.
    """


class NumIterationsGetterFromSequence:
    def __init__(self, seq_num_iterations):
        self.seq_num_iterations = seq_num_iterations
        self.idx = -1

    def __call__(self, **kwargs):
        self.idx += 1
        try:
            return self.seq_num_iterations[self.idx]
        except IndexError:
            raise NumIterationsSequenceExhausted(
                f"num_iterations sequence has been exhausted: {self.seq_num_iterations}"
            )


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

    def get_loop_variables_at_level_or_above(self, loop_level):
        res = dict()
        for cur_level in range(loop_level, self.max_level + 1):
            res.update(self.get_loop_variables_at_level(cur_level))
        return res

    def run_loop_iterations_with(self, f_run_iteration):
        return self._run_loop_iterations_impl(f_run_iteration, self.max_level)

    def _run_loop_iterations_impl(self, f_run_iteration, cur_loop_level, **loop_var_values_at_higher_levels):
        if cur_loop_level == 0:
            try:
                yield from f_run_iteration(**loop_var_values_at_higher_levels)
            except NumIterationsSequenceExhausted:
                return
        else:
            for cur_vals in self.iter_loop_var_values_at_level(cur_loop_level):
                yield from self._run_loop_iterations_impl(
                    f_run_iteration, cur_loop_level=cur_loop_level - 1, **cur_vals, **loop_var_values_at_higher_levels
                )

    def iter_loop_var_values_at_level(self, loop_level):
        """
        Yield a sequence of dictionaries of the form `{name: value}`, where
        `value` iterates through the possible values for the loop variable
        with name `name`.

        Examples
        --------
        >>> loop_runner.iter_loop_var_values_at_level(loop_level=1)
        [{"x": 111, "y": "AAA"},
         {"x": 222, "y": "BBB"},
         {"x": 333, "y": "CCC"}]
        """
        loop_vars_at_level = self.get_loop_variables_at_level(loop_level)
        var_names = list(loop_vars_at_level)
        all_var_values = zip(*(x.values for x in loop_vars_at_level.values()))
        for vals in all_var_values:
            yield dict(zip(var_names, vals))

    def _get_loop_iteration_lengths_impl(self, num_iterations):
        get_num_iterations_at_level_0 = make_num_iterations_getter(num_iterations)

        def f_do_stuff(**kwargs):
            try:
                yield (kwargs, get_num_iterations_at_level_0(**kwargs))
            except StopIteration:
                return

        return self.run_loop_iterations_with(f_do_stuff)

    def get_loop_iteration_lengths(self, num_iterations, loop_level=1):
        if loop_level < 1 or loop_level > self.max_level:
            raise ValueError(
                f"The value of loop_level must be in the range 1 <= loop_level <= {self.max_level}. Got: {loop_level}"
            )

        vars_at_level_or_above = list(self.get_loop_variables_at_level_or_above(loop_level))

        def key_func(loop_var_values):
            return {name: loop_var_values[0][name] for name in vars_at_level_or_above}

        for k, g in groupby(self._get_loop_iteration_lengths_impl(num_iterations), key_func):
            yield (k, sum([x[1] for x in g]))
