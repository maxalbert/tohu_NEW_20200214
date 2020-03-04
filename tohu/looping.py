from collections import defaultdict
from typing import Sequence
from .base import TohuBaseGenerator

__all = ["LoopVariable", "LoopRunner"]


def is_sequence(seq):
    return isinstance(seq, Sequence) and not isinstance(seq, str)


class UnassignedValuesError(Exception):
    pass


class LoopVariable(TohuBaseGenerator):
    def __init__(self, name, values=None):
        super().__init__()
        self.name = name
        self._loop_level = None
        self.assign_values(values)

    def __repr__(self):
        return f"<LoopVariable: {self.name!r}, level={self.loop_level}, values={self.values} (id={self.tohu_id})>"

    @property
    def loop_level(self):
        return self._loop_level

    @loop_level.setter
    def loop_level(self, value):
        if value < 1:
            raise ValueError(f"Loop level must be >= 1 (got: {value})")
        self._loop_level = value

    def assign_values(self, values):
        if values is not None and (not isinstance(values, Sequence) or isinstance(values, str)):
            raise TypeError(f"Argument `values` must be a list, tuple, or similar sequence type. Got: {type(values)}")

        if values:
            self.values = values
            self.idx = 0
            self.cur_value = self.values[0]
            self.has_values_assigned = True
            self.is_hidden = True
        else:
            self.values = None
            self.idx = None
            self.cur_value = None
            self.has_values_assigned = False
            self.is_hidden = True

    def __next__(self):
        return self.cur_value

    def reset(self, seed=None):
        if not self.has_values_assigned:
            raise UnassignedValuesError(f"Loop variable {self.name!r} has not been assigned any values.")

        # Note: There are two options for what reset() can do in a LoopVariable.
        # Currently we reset it to its first value (which is consistent with the
        # reset behaviour of other tohu generators). As a consequence, we can only
        # reset the custom generator inside a ForeachGeneratorInstance once at the
        # very beginning of the loop.
        # This is totally fine. Another option would be to reset it once at the
        # beginning of each loop iteration (with a different internal seed, of
        # course), but then we'd probably need to make this reset() method a no-op
        # and add an additional method such as `reset_loop_variable()` which needs
        # to be called at the very beginning of the loop. There may be advantages
        # to this approach, but it feels slightly less consistent across tohu
        # generators, so for now we choose this approach.
        super().reset(seed)
        self.idx = 0
        self.cur_value = self.values[0]

    def advance(self):
        if not self.has_values_assigned:
            raise UnassignedValuesError(f"Loop variable {self.name!r} has not been assigned any values.")

        self.idx += 1
        try:
            self.cur_value = self.values[self.idx]
        except IndexError:
            raise IndexError("Loop variable has been exhausted.")

        # TODO: Should advancing of clones happen before we raise the
        #       IndexError above, or afterwards, or does it not matter?
        for c in self.clones:
            c.advance()

    def spawn(self, gen_mapping=None):
        new_obj = LoopVariable(self.name, self.values)
        new_obj._set_state_from(self)
        return new_obj

    def _set_state_from(self, other):
        self.idx = other.idx
        self.cur_value = other.cur_value
        self.loop_level = other.loop_level


class LoopRunner:
    def __init__(self):
        self.loop_variables_per_level = defaultdict(list)
        self.loop_variables = {}
        self.max_level = 0

    def add_loop_variable(self, name, loop_variable):
        # Check constraints on `level` argument to ensure levels
        #  are contiguous between 1 and max_level.
        level = loop_variable.loop_level
        # if level > self.max_level + 1:
        #     raise ValueError(
        #         f"Level must be at most <= max_level + 1. " f"Got: level={level}, max_level={self.max_level}."
        #     )

        self.max_level = max(self.max_level, level)
        self.loop_variables_per_level[level].append(name)
        self.loop_variables[name] = loop_variable

    def get_loop_var_values(self):
        return {name: x.cur_value for name, x in self.loop_variables.items()}

    @property
    def unassigned_variables(self):
        unassigned_vars = []
        for name, var in self.loop_variables.items():
            if not var.has_values_assigned:
                unassigned_vars.append(name)
        return unassigned_vars

    @property
    def has_unassigned_variables(self):
        return self.unassigned_variables != []

    def assign_values(self, name, values):
        self.loop_variables[name].assign_values(values)

    def advance_loop_vars_at_level(self, level):
        for name in self.loop_variables_per_level[level]:
            self.loop_variables[name].advance()

    def reset_loop_vars_below_level(self, level):
        for cur_level in range(1, level):
            for name in self.loop_variables_per_level[cur_level]:
                self.loop_variables[name].reset()

    def run_loop_to_generate_items_with(self, g, num_iterations):
        # TODO: add sanity check that loop variable levels take all the values between 1 and max_level?

        if self.has_unassigned_variables:
            raise UnassignedValuesError(
                f"LoopRunner has variables with unassigned values: {', '.join(self.unassigned_variables)}"
            )

        def ensure_callable(num_iterations):
            if callable(num_iterations):
                return num_iterations
            elif isinstance(num_iterations, int):

                def constant_func(**kwargs):
                    return num_iterations

                return constant_func
            elif is_sequence(num_iterations):
                raise NotImplementedError("TODO: Implement me!")
            else:
                raise TypeError(f"Unsupported type for `num_iterations`: {type(num_iterations)}")

        f_num_iterations = ensure_callable(num_iterations)

        yield from self._run_loop_impl(g, f_num_iterations, self.max_level)

    def _run_loop_impl(self, g, f_num_iterations, cur_level):
        # TODO: Reset generators within each loop iteration?! Should this happen here or somewhere else?!?
        cur_loop_var_values = self.get_loop_var_values()

        if cur_level == 0:
            num_iterations = f_num_iterations(**cur_loop_var_values)
            yield from g.generate(num=num_iterations)
        else:
            while True:
                self.reset_loop_vars_below_level(cur_level)
                yield from self._run_loop_impl(g, f_num_iterations, cur_level - 1)
                try:
                    self.advance_loop_vars_at_level(cur_level)
                except IndexError:
                    break
