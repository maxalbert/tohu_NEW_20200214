import itertools
from typing import Callable, List
from .base import SeedGenerator, TohuBaseGenerator
from .logging import logger
from .num_iterations_specifier import make_num_iterations_specifier, NumIterationsSpecifier


def concatenate_tuples(list_of_tuples):
    """
    Helper function to combine multiple tuples into a single one.
    """
    return sum(list_of_tuples, ())


class LoopVariableExhaustedNEW3(Exception):
    """
    Custom exception to indicate that a loop variable
    has iterated through all its values.
    """


class LoopVariableNEW3Iterator:
    """
    This class allows iterating over the values of a loop variable
    while optionally updating the internal state during iteration.
    """

    def __init__(self, loop_var, *, advance=False):
        self.loop_var = loop_var
        self.advance = advance

    def __iter__(self):
        if self.advance:
            self.loop_var.rewind_loop_variable()

        for val in self.loop_var.values:
            logger.debug(f"{self.loop_var}, current value: {self.loop_var.cur_value}")
            yield (self.loop_var.name, val)
            if self.advance:
                try:
                    self.loop_var.advance()
                except LoopVariableExhaustedNEW3:
                    return


class LoopVariableNEW3(TohuBaseGenerator):
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

    @property
    def name_paired_with_values(self):
        return [(self.name, x) for x in self.values]

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
            raise LoopVariableExhaustedNEW3(f"Loop variable has been exhausted: {self}")

        for c in self.clones:
            c.advance()

    def rewind_loop_variable(self):
        self.idx = 0
        self.cur_value = self.values[0]

        for c in self.clones:
            c.rewind_loop_variable()

    # def iter_values_and_optionally_advance(self, *, advance=False):
    #     # Note that if `advance` is False, we could simply return (or yield from)
    #     # self.values here since there are no side-effects. However, if `advance`
    #     # is True then we want to make sure the internal state of this loop variable
    #     # is updated every time the caller iterates over the returned values. Since
    #     # the caller may choose to iterate multiple times, we need to return a special
    #     # iterator which deals with updating the internal state during each iteration.
    #     return LoopVariableNEW3Iterator(self, advance=advance)

    def update_current_value(self, value):
        if value not in self.values:
            raise ValueError(f"Invalid value for {self}: {value}")

        self.idx = self.values.index(value)
        self.cur_value = value

        for c in self.clones:
            c.update_current_value(value)

    def spawn(self, gen_mapping=None):
        return self.__class__(self.name, self.values).set_loop_level(self.loop_level)


class LoopRunnerNEW3:
    """
    The responsibility of this class is to manage a collection loop variables
    and to orchestrate some action based on the possible combinations of
    their values.

    There are two kinds of "iteration" related to a loop runner. First,
    there is the iteration that consists of cycling through all combinations
    of loop variable values. We refer to each such combination (and the
    action(s) that happen for it) as a "loop cycle" (or simply "cycle").
    Second, there are the "subordinate" or "inner" loop iterations that are
    coordinated by the loop runner for a fixed combination of loop variable
    values (these typically happen via some callback function and are outside
    the direct control of the loop runner but are orchestrated by it). To
    avoid confusion in the terminology and because the term "iteration" is
    ambiguous, we refer to these inner iterations as "ticks" (for lack of a
    better term).

    In summary, a loop runner represents a nested loop of the following
    structure:

       for x_1 in values_1:                     ---.
           for x_2 in values_2:                    |      each combination of
                for x_3 in values_3:               |--->  values of x_1, ..., x_n
                   ...                             |      represents a loop cycle
                   for x_n in values_n:         ---.
                       # This is where the "inner" loop starts. Any
                       # iterations that are performed by the function
                       # f_callback are referred to as "ticks".
                       f_callback(num_iterations, **loop_var_values)

    Note that the above loop structure is slightly simplified because we allow
    iterating over multiple loop variables simultaneously at the same level. So
    any of the lines

       for x_i in values_i:

    can be replaced with the following more general one:

       for (x_i, y_i, ...) in zip(values_x_i, values_y_i, ...)

    Note that the implementation of the this class assumes that there are
    only comparatively few loop variable values and combinations to cycle
    through and that the bulk of the work
    happens inside f_callback in the innermost part of the loop. If this assumption does not hold execution may not be very effi
    """

    def __init__(self):
        self.loop_variables_by_level = {}
        self.loop_variables_by_name = {}

    def add_loop_variables_at_level(self, loop_vars, *, level):
        assert isinstance(loop_vars, dict)
        self.loop_variables_by_level[level] = [x.set_loop_level(level) for x in loop_vars.values()]
        # TODO: check none of the new names exist yet!
        self.loop_variables_by_name.update(loop_vars)

    def spawn(self):
        new_loop_runner = LoopRunnerNEW3()
        dep_mapping = {}
        for level, vars_for_level in self.loop_variables_by_level.items():
            spawned_loop_vars = []
            for x in vars_for_level:
                x_spawned = x.spawn()
                spawned_loop_vars.append(x_spawned)
                dep_mapping[x] = x_spawned
            # new_loop_runner.loop_variables_by_level[level] = spawned_loop_vars
            new_loop_runner.add_loop_variables_at_level({x.name: x for x in spawned_loop_vars}, level=level)
        return new_loop_runner, dep_mapping

    @property
    def loop_variables(self):
        return sum(self.loop_variables_by_level.values(), [])

    # @property
    # def max_loop_level(self):
    #     return max(self.loop_variables_by_level.keys())

    def rewind_all_loop_variables(self):
        """
        Rewind all loop variables in this loop runner to their initial values.
        """
        for x in self.loop_variables:
            x.rewind_loop_variable()

    def produce_items_from_tohu_generator(self, g, num_items_per_loop_cycle, seed):
        # seed_generator = SeedGenerator()
        # seed_generator.reset(seed)

        def f_callback(num_items, cur_seed, **kwargs):
            g.reset(cur_seed)
            yield from g.generate_as_list(num=num_items)

        yield from self.iter_loop_var_combinations_with_callback(
            f_callback, num_items_per_loop_cycle, seed=seed, advance_loop_vars=True
        )

    def update_loop_variable_values(self, loop_var_values):
        assert isinstance(loop_var_values, dict)
        for name, value in loop_var_values.items():
            self.loop_variables_by_name[name].update_current_value(value)

    def iter_loop_var_combinations_with_callback(
        self,
        f_callback: Callable,
        num_ticks_per_loop_cycle: NumIterationsSpecifier,
        seed: int = None,
        advance_loop_vars: bool = False,
    ):
        """
        Iterate over all combinations of loop variable values and invoke a callback function for each.

        Parameters
        ----------
        f_callback : Callable
            Callback function which is invoked for each combination of loop variable values.
            This must accept three arguments:
              - the current number of iterations (passed as a positional argument)
              - the current seed (passed as a positional argument)
              - the current loop variable values as the remaining arguments (passed as keyword arguments)
            It must return an iterable.

        num_ticks_per_loop_cycle : NumIterationsSpecifier
            Specifier for the number of "ticks" of the innermost loop for with each combination
            of loop variable values.

        Returns
        -------
        Iterable
            The concatenation of the iterables obtained from all invocations of `f_callback`.
        """
        for (
            loop_var_values,
            num_items,
            cur_seed,
        ) in self.iter_loop_var_combinations_with_num_ticks_and_seed_for_each_loop_cycle(
            num_ticks_per_loop_cycle, initial_seed=seed
        ):
            if advance_loop_vars:
                self.update_loop_variable_values(loop_var_values)

            yield from f_callback(num_items, cur_seed, **loop_var_values)

    def iter_loop_var_combinations_with_num_ticks_and_seed_for_each_loop_cycle(
        self, num_ticks_per_loop_cycle: NumIterationsSpecifier, initial_seed: int, var_names: List[str] = None
    ):
        num_ticks_per_loop_cycle = make_num_iterations_specifier(num_ticks_per_loop_cycle)
        var_names = var_names or [x.name for x in self.loop_variables]

        seed_generator = SeedGenerator()
        seed_generator.reset(initial_seed)

        for cur_vals in self.iter_loop_var_combinations():
            # TODO: have a think about whether we should construct a more specific seed for
            #       each loop cycle that incorporates the current loop variable values.
            cur_seed = next(seed_generator)
            yield cur_vals, num_ticks_per_loop_cycle(**cur_vals), cur_seed

    # def iter_loop_var_combinations(self, var_names=None):
    def iter_loop_var_combinations(self):
        """
        Return all combinations of values of the loop variables present in this
        loop runner (or of the loop variables in `var_names` if specified).

        Returns
        -------
        Iterable
            Iterable containing all possible combinations of loop variable values.
        """
        value_combinations_per_level = (
            zip(*(loop_var.name_paired_with_values for loop_var in self.loop_variables_by_level[level]))
            for level in reversed(sorted(self.loop_variables_by_level.keys()))
        )

        for val_comb in itertools.product(*value_combinations_per_level):
            yield dict(concatenate_tuples(val_comb))

    def get_total_number_of_ticks(self, *, num_ticks_per_loop_cycle):
        num_ticks_for_individual_loop_cycles = [
            num
            for _, num in self.iter_loop_var_combinations_with_num_ticks_per_loop_cycle(
                num_ticks_per_loop_cycle=num_ticks_per_loop_cycle
            )
        ]
        return sum(num_ticks_for_individual_loop_cycles)
