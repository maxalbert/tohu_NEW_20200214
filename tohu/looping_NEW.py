from itertools import groupby
from .base import TohuBaseGenerator
from .num_iterations_specifier import (
    make_num_iterations_specifier,
    NumIterationsSpecifier,
    NumIterationsSequenceExhausted,
)

__all__ = ["LoopVariableNEW", "is_loop_variable"]


def is_loop_variable(g):
    return isinstance(g, LoopVariableNEW)


class LoopVariableExhaustedNEW(Exception):
    """
    Custom exception to indicate that a loop variable
    has iterated through all its values.
    """


class LoopExhaustedNEW(Exception):
    """
    Custom exception to indicate that a loop has iterated
    through combinations of values of its loop variables.
    """


class LoopVariableNEW(TohuBaseGenerator):
    def __init__(self, name, values):
        super().__init__()
        self.name = name
        self.values = values
        self.loop_level = None

        self.idx = 0
        self.cur_value = values[0]

    def __repr__(self):
        return (
            f"<LoopVariable: name={self.name!r}, loop_level={self.loop_level}, "
            f"values={self.values!r}, cur_value={self.cur_value!r} (tohu_id={self.tohu_id})>"
        )

    def set_loop_level(self, level):
        self.loop_level = level
        return self

    def __next__(self):
        return self.cur_value

    def advance(self):
        self.idx += 1
        try:
            self.cur_value = self.values[self.idx]
        except IndexError:
            raise LoopVariableExhaustedNEW(f"Loop variable has been exhausted: {self}")

        for c in self.clones:
            c.advance()

    def rewind_loop_variable(self):
        self.idx = 0
        self.cur_value = self.values[0]

        for c in self.clones:
            c.rewind_loop_variable()

    def spawn(self, gen_mapping=None):
        return self.__class__(self.name, self.values).set_loop_level(self.loop_level)


class LoopRunnerNEW:
    def __init__(self):
        self.loop_variables = {}
        self.max_loop_level = 0

    def add_loop_variable(self, x: LoopVariableNEW, level: int = None):
        level = level or x.loop_level

        if level is None:
            raise ValueError("Loop variable must have `loop_level` set, or `level` argument must be given.")

        if x.name in self.loop_variables:
            raise ValueError(f"A loop variable with name {x.name!r} already exists.")

        x.set_loop_level(level)
        self.loop_variables[x.name] = x
        self.max_loop_level = max(level, self.max_loop_level)

    def print_current_loop_var_values(self):
        """
        Helper function which displays the current loop variable values.
        """
        print({name: x.cur_value for name, x in self.loop_variables.items()})

    def get_loop_vars_at_level(self, loop_level: int):
        return {name: x for (name, x) in self.loop_variables.items() if x.loop_level == loop_level}

    def get_loop_vars_at_level_and_above(self, loop_level: int):
        return {name: x for (name, x) in self.loop_variables.items() if x.loop_level >= loop_level}

    def rewind_all_loop_variables(self):
        for _, x in self.loop_variables.items():
            x.rewind_loop_variable()

    def rewind_loop_vars_at_level(self, loop_level: int):
        for _, x in self.get_loop_vars_at_level(loop_level).items():
            x.rewind_loop_variable()

    def advance_loop_variables(self, loop_level: int = 1):
        if loop_level > self.max_loop_level:
            raise LoopExhaustedNEW("Loop has been exhausted.")

        try:
            for _, x in self.get_loop_vars_at_level(loop_level).items():
                x.advance()
        except LoopVariableExhaustedNEW:
            self.rewind_loop_vars_at_level(loop_level)
            self.advance_loop_variables(loop_level + 1)

    def iter_loop_var_combinations(self, var_names=None):
        if var_names is None or list(var_names) == []:
            yield from self._iter_loop_var_value_combinations_impl(self.max_loop_level)
        else:
            seen = set()
            for x in (tuple((name, x[name]) for name in var_names) for x in self.iter_loop_var_combinations()):
                if x not in seen:
                    seen.add(x)
                    yield dict(x)

    def _iter_loop_var_value_combinations_impl(self, cur_level, **loop_var_values_at_higher_levels):
        if cur_level == 0:
            yield loop_var_values_at_higher_levels
        else:
            for cur_loop_var_values in self._iter_loop_var_combinations_at_level(cur_level):
                yield from self._iter_loop_var_value_combinations_impl(
                    cur_level - 1, **cur_loop_var_values, **loop_var_values_at_higher_levels
                )

    def _iter_loop_var_combinations_at_level(self, loop_level: int):
        loop_vars_at_level = self.get_loop_vars_at_level(loop_level)
        var_names = loop_vars_at_level.keys()

        for cur_vals in zip(*[x.values for _, x in loop_vars_at_level.items()]):
            yield dict(zip(var_names, cur_vals))

    def iter_loop_var_combinations_with_num_iterations(
        self, num_iterations: NumIterationsSpecifier, loop_level: int = 1
    ):
        assert 1 <= loop_level and loop_level <= self.max_loop_level
        if loop_level == 1:
            yield from self._iter_loop_var_combinations_with_num_iterations_at_level_1(num_iterations)
        else:
            loop_var_names_at_level_and_above = list(self.get_loop_vars_at_level_and_above(loop_level))

            def key_func(loop_var_values_and_num_iterations):
                loop_var_values = loop_var_values_and_num_iterations[0]
                return {
                    name: value
                    for (name, value) in loop_var_values.items()
                    if name in loop_var_names_at_level_and_above
                }

            data = self.iter_loop_var_combinations_with_num_iterations(num_iterations, loop_level=1)
            grouped_data = groupby(data, key=key_func)
            for key, grp in grouped_data:
                num_iterations = [x[1] for x in grp]
                yield key, sum(num_iterations)

    def _iter_loop_var_combinations_with_num_iterations_at_level_1(self, num_iterations: NumIterationsSpecifier):
        num_iterations = make_num_iterations_specifier(num_iterations)
        for loop_var_values in self.iter_loop_var_combinations():
            try:
                yield loop_var_values, num_iterations(**loop_var_values)
            except NumIterationsSequenceExhausted:
                return

    # def spawn(self):
    #     new_loop_runner = LoopRunnerNEW()
    #     for x in self.loop_variables.values():
    #         new_loop_runner.add_loop_variable(x, x.loop_level)
    #     return new_loop_runner
