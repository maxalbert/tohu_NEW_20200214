from itertools import groupby

from .base import TohuBaseGenerator

__all__ = ["LoopVariable", "LoopRunner"]


class LoopVariableExhausted(Exception):
    """
    Custom exception to indicate that a loop variable has iterated through all its values.
    """


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
            raise LoopVariableExhausted(f"Loop variable has been exhausted: {self}")

        for c in self.clones:
            c.advance()

    def reset_loop_variable(self):
        self.idx = 0
        self.cur_value = self.values[0]

        for c in self.clones:
            c.reset_loop_variable()

    def set_loop_level(self, loop_level):
        self.loop_level = loop_level

        for c in self.clones:
            c.set_loop_level(loop_level)

        return self

    def spawn(self, gen_mapping=None):
        return LoopVariable(self.name, self.values).set_loop_level(self.loop_level)


class LoopRunner:
    def __init__(self, loop_variables):
        self.loop_variables = loop_variables
        self.max_level = max([x.loop_level for _, x in self.loop_variables.items()])

    def get_loop_vars_at_level(self, loop_level):
        return {name: x for (name, x) in self.loop_variables.items() if x.loop_level == loop_level}

    def get_loop_vars_at_level_and_above(self, loop_level):
        return {name: x for (name, x) in self.loop_variables.items() if x.loop_level >= loop_level}

    def iter_loop_var_combinations_at_level(self, loop_level):
        loop_vars_at_level = self.get_loop_vars_at_level(loop_level)
        var_names = loop_vars_at_level.keys()

        for cur_vals in zip(*[x.values for _, x in loop_vars_at_level.items()]):
            yield dict(zip(var_names, cur_vals))

    def iter_loop_var_combinations(self):
        yield from self._iter_loop_var_value_combinations_impl(self.max_level)

    def _iter_loop_var_value_combinations_impl(self, cur_level, **loop_var_values_at_higher_levels):
        if cur_level == 0:
            yield loop_var_values_at_higher_levels
        else:
            for cur_loop_var_values in self.iter_loop_var_combinations_at_level(cur_level):
                yield from self._iter_loop_var_value_combinations_impl(
                    cur_level - 1, **cur_loop_var_values, **loop_var_values_at_higher_levels
                )

    def iter_loop_var_combinations_with_num_iterations(self, f_num_iterations, loop_level=1):
        assert 1 <= loop_level and loop_level <= self.max_level
        if loop_level == 1:
            yield from self._iter_loop_var_combinations_with_num_iterations_at_level_1(f_num_iterations)
        else:
            loop_var_names_at_level_and_above = list(self.get_loop_vars_at_level_and_above(loop_level))

            def key_func(loop_var_values_and_num_iterations):
                loop_var_values = loop_var_values_and_num_iterations[0]
                return {
                    name: value
                    for (name, value) in loop_var_values.items()
                    if name in loop_var_names_at_level_and_above
                }

            data = self.iter_loop_var_combinations_with_num_iterations(f_num_iterations, loop_level=1)
            grouped_data = groupby(data, key=key_func)
            for key, grp in grouped_data:
                num_iterations = [x[1] for x in grp]
                yield key, sum(num_iterations)

    def _iter_loop_var_combinations_with_num_iterations_at_level_1(self, f_num_iterations):
        assert callable(f_num_iterations)
        for loop_var_values in self.iter_loop_var_combinations():
            yield loop_var_values, f_num_iterations(**loop_var_values)

    def iter_loop_var_combinations_with_callback(self, f_callback, f_num_iterations, loop_level=1):
        for loop_var_values, num_iterations in self.iter_loop_var_combinations_with_num_iterations(
            f_num_iterations, loop_level
        ):
            yield from f_callback(num_iterations, **loop_var_values)
