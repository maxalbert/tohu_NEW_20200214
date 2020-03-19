from itertools import groupby
from string import Formatter
from typing import Callable, Dict, Optional

from .base import TohuBaseGenerator, SeedGenerator

__all__ = ["LoopVariable", "LoopRunner"]


class LoopVariableExhausted(Exception):
    """
    Custom exception to indicate that a loop variable
    has iterated through all its values.
    """


class LoopExhausted(Exception):
    """
    Custom exception to indicate that a loop has iterated
    through combinations of values of its loop variables.
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
    def __init__(self, loop_variables: Optional[Dict[str, LoopVariable]] = None):
        if loop_variables is None:
            self.loop_variables = {}
            self.max_level = 0
        else:
            self.loop_variables = loop_variables
            self.max_level = max([x.loop_level for _, x in self.loop_variables.items()])

    def add_loop_variable(self, name, loop_variable):
        level = loop_variable.loop_level
        self.max_level = max(self.max_level, level)
        self.loop_variables[name] = loop_variable

    def get_loop_vars_at_level(self, loop_level: int):
        return {name: x for (name, x) in self.loop_variables.items() if x.loop_level == loop_level}

    def get_loop_vars_at_level_and_above(self, loop_level: int):
        return {name: x for (name, x) in self.loop_variables.items() if x.loop_level >= loop_level}

    def iter_loop_var_combinations_at_level(self, loop_level: int):
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

    def iter_loop_var_combinations_with_num_iterations(self, f_num_iterations: Callable, loop_level: int = 1):
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

    def _iter_loop_var_combinations_with_num_iterations_at_level_1(self, f_num_iterations: Callable):
        assert callable(f_num_iterations)
        for loop_var_values in self.iter_loop_var_combinations():
            yield loop_var_values, f_num_iterations(**loop_var_values)

    def iter_loop_var_combinations_with_callback(self, f_callback: Callable, f_num_iterations: Callable, loop_level=1):
        for loop_var_values, num_iterations in self.iter_loop_var_combinations_with_num_iterations(
            f_num_iterations, loop_level
        ):
            yield from f_callback(num_iterations, **loop_var_values)

    def print_current_loop_var_values(self):
        """
        Helper function which displays the current loop variable values.
        """
        print({name: x.cur_value for name, x in self.loop_variables.items()})

    def reset_all_loop_variables(self):
        for _, x in self.loop_variables.items():
            x.reset_loop_variable()

    def reset_loop_vars_at_level(self, loop_level):
        for _, x in self.get_loop_vars_at_level(loop_level).items():
            x.reset_loop_variable()

    def advance_loop_variables(self, loop_level=1):
        if loop_level > self.max_level:
            raise LoopExhausted("Loop has been exhausted.")

        try:
            for _, x in self.get_loop_vars_at_level(loop_level).items():
                x.advance()
        except LoopVariableExhausted:
            self.reset_loop_vars_at_level(loop_level)
            self.advance_loop_variables(loop_level + 1)

    def iter_loop_var_combinations_with_generator(
        self, g: TohuBaseGenerator, f_num_iterations: Callable, seed: Optional[int] = None
    ):

        seed_generator = SeedGenerator()
        if seed is not None:
            seed_generator.reset(seed)

        def f_callback(num_iterations, **kwargs):
            g.reset(next(seed_generator))
            # TODO: reset `g` during each iteration?!
            yield from g.generate_as_list(num=num_iterations)
            try:
                self.advance_loop_variables()
            except LoopExhausted:
                return

        self.reset_all_loop_variables()
        yield from self.iter_loop_var_combinations_with_callback(f_callback, f_num_iterations)

    def iter_loop_var_combinations_with_filename_pattern(self, filename_pattern: str):
        fmt_lst = list(Formatter().parse(filename_pattern))
        param_names = [field_name for (_, field_name, _, _) in fmt_lst if field_name is not None]
        filenames = []
        for loop_var_values in self.iter_loop_var_combinations():
            param_values = {name: value for name, value in loop_var_values.items() if name in param_names}
            cur_filename = filename_pattern.format(**param_values)
            if cur_filename not in filenames:
                filenames.append(cur_filename)
        return filenames
