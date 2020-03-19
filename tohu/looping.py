from itertools import groupby
from string import Formatter
from typing import Callable, Dict, Optional, Sequence, Union

from .base import TohuBaseGenerator, SeedGenerator
from .logging import logger

__all__ = ["LoopVariable", "LoopRunner", "PLACEHOLDER"]

# Alias for unassigned loop variable values, for potentially better readability in @foreach decorators.
PLACEHOLDER = Ellipsis

NumIterationsSpecifier = Union[int, Sequence[int], Callable]


class NumIterationsSequenceExhausted(Exception):
    """
    Custom exception to indicate that a `num_iterations` sequence has been exhausted.
    """


class NumIterationsSpecifierFromCallable:
    def __init__(self, func_num_iterations: Callable):
        self.func_num_iterations = func_num_iterations

    def __call__(self, **kwargs):
        return self.func_num_iterations(**kwargs)


class NumIterationsSpecifierFromInt:
    def __init__(self, num_iterations: int):
        self.num_iterations = num_iterations

    def __call__(self, **kwargs):
        return self.num_iterations


class NumIterationsSpecifierFromSequence:
    def __init__(self, seq_num_iterations: Sequence[int]):
        self.seq_num_iterations = seq_num_iterations
        self.idx = -1

    def __call__(self, **kwargs):
        self.idx += 1
        try:
            return self.seq_num_iterations[self.idx]
        except IndexError:
            logger.warn(
                f"num_iterations sequence does not contain enough elements to complete loop: {self.seq_num_iterations}"
            )
            raise NumIterationsSequenceExhausted(
                f"num_iterations sequence has been exhausted: {self.seq_num_iterations}"
            )


def make_num_iterations_specifier(num_iterations):
    if isinstance(num_iterations, Callable):
        return NumIterationsSpecifierFromCallable(num_iterations)
    elif isinstance(num_iterations, int):
        return NumIterationsSpecifierFromInt(num_iterations)
    elif isinstance(num_iterations, Sequence):
        return NumIterationsSpecifierFromSequence(num_iterations)
    else:
        raise TypeError("Invalid type for argument `num_iterations`. Must be one of: integer, sequence, callable")


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


class UnassignedValuesError(Exception):
    """
    Custom exception to indicate that a loop variable has not been assigned any values.
    """


class LoopVariable(TohuBaseGenerator):
    def __init__(self, name, values=None):
        super().__init__()
        self.name = name
        self.loop_level = None
        self.is_hidden = True
        self.assign_values(values)

    def assign_values(self, values):
        if values is Ellipsis:
            values = None

        if values is not None and (not isinstance(values, Sequence) or isinstance(values, str)):
            raise TypeError(f"Argument `values` must be a list, tuple, or similar sequence type. Got: {type(values)}")

        if values:
            self._values = values
            self.idx = 0
            self.cur_value = self._values[0]
            self.has_values_assigned = True
        else:
            self._values = None
            self.idx = None
            self.cur_value = None
            self.has_values_assigned = False

        for c in self.clones:
            c.assign_values(values)

    def __next__(self):
        return self.cur_value

    def __repr__(self):
        return f"<LoopVariable: name={self.name!r}, loop_level={self.loop_level!r}, values={self._values!r}, cur_value={self.cur_value!r}>"

    @property
    def values(self):
        if self._values is not None:
            return self._values
        else:
            raise UnassignedValuesError(f"Loop variable '{self.name}' has not been assigned any values.")

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
        return LoopVariable(self.name, self._values).set_loop_level(self.loop_level)


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

    def iter_loop_var_combinations_with_num_iterations(
        self, num_iterations: NumIterationsSpecifier, loop_level: int = 1
    ):
        assert 1 <= loop_level and loop_level <= self.max_level
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

    def iter_loop_var_combinations_with_callback(
        self, f_callback: Callable, num_iterations: NumIterationsSpecifier, loop_level=1
    ):
        for loop_var_values, num_iterations in self.iter_loop_var_combinations_with_num_iterations(
            num_iterations, loop_level
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
        self, g: TohuBaseGenerator, num_iterations: NumIterationsSpecifier, seed: int
    ):

        seed_generator = SeedGenerator()
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
        yield from self.iter_loop_var_combinations_with_callback(f_callback, num_iterations)

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
