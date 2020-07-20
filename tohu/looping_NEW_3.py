from typing import Callable
from .base import SeedGenerator, TohuBaseGenerator
from .logging import logger
from .num_iterations_specifier import make_num_iterations_specifier, NumIterationsSpecifier


class StatefulZip:
    """
    This class represents an implementation of `zip` which:

    1) allows multiple iterations over the result (as would `list(zip(...))`)
    2) ensures that every time we iterate over the result, we also iterate
       over the individual iterables that were passed as arguments

    Note that this is not very efficient, but we only use it for sequences of
    loop variable values where performance is not a concern because they
    typically only contain a few values. However, property (2) is essential
    in case we need to update the internal state of the loop variables during
    iteration (e.g. when `iter_values_and_optionally_advance()` is called).
    """

    def __init__(self, *iterables):
        self.iterables = iterables

    def __iter__(self):
        yield from zip(*self.iterables)


def product_of_iterables(*iterables):
    """
    This provides essentially the same functionality as itertools.product,
    except that it iterates over the input iterables every time in the
    "nested for loop". This is essential to correctly update the internal
    state of loop variables.
    """
    if iterables == ():
        yield ()
    else:
        cur_seq = iterables[0]
        remaining_seqs = iterables[1:]
        for z in cur_seq:
            for tup in product_of_iterables(*remaining_seqs):
                yield (z,) + tup


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

    def iter_values_and_optionally_advance(self, *, advance=False):
        # Note that if `advance` is False, we could simply return (or yield from)
        # self.values here since there are no side-effects. However, if `advance`
        # is True then we want to make sure the internal state of this loop variable
        # is updated every time the caller iterates over the returned values. Since
        # the caller may choose to iterate multiple times, we need to return a special
        # iterator which deals with updating the internal state during each iteration.
        return LoopVariableNEW3Iterator(self, advance=advance)

    def spawn(self, gen_mapping=None):
        return self.__class__(self.name, self.values).set_loop_level(self.loop_level)


class LoopRunnerNEW3:
    def __init__(self):
        self.loop_variables_by_level = {}

    def add_loop_variables_at_level(self, loop_vars, *, level):
        assert isinstance(loop_vars, dict)
        self.loop_variables_by_level[level] = [x.set_loop_level(level) for x in loop_vars.values()]

    def spawn(self):
        new_loop_runner = LoopRunnerNEW3()
        dep_mapping = {}
        for level, vars_for_level in self.loop_variables_by_level.items():
            spawned_loop_vars = []
            for x in vars_for_level:
                x_spawned = x.spawn()
                spawned_loop_vars.append(x_spawned)
                dep_mapping[x] = x_spawned
            new_loop_runner.loop_variables_by_level[level] = spawned_loop_vars
        return new_loop_runner, dep_mapping

    @property
    def loop_variables(self):
        return sum(self.loop_variables_by_level.values(), [])

    @property
    def max_loop_level(self):
        return max(self.loop_variables_by_level.keys())

    def rewind_all_loop_variables(self):
        """
        Rewind all loop variables in this loop runner to their initial values.
        """
        for x in self.loop_variables:
            x.rewind_loop_variable()

    def produce_items_from_tohu_generator(self, g, num_items_per_loop_iteration, seed):
        seed_generator = SeedGenerator()
        seed_generator.reset(seed)

        def f_callback(num_items, **kwargs):
            g.reset(next(seed_generator))
            yield from g.generate_as_list(num=num_items)

        yield from self.iter_loop_var_combinations_with_callback(
            f_callback, num_items_per_loop_iteration, advance_loop_vars=True
        )

    def iter_loop_var_combinations_with_callback(
        self,
        f_callback: Callable,
        num_items_per_loop_iteration: NumIterationsSpecifier,
        advance_loop_vars: bool = False,
    ):
        """
        Iterate over all combinations of loop variable values and invoke a callback function for each.

        Parameters
        ----------
        f_callback : Callable
            Callback function which is invoked for each combination of loop variable values.
            This must accept the current number of iterations as the first argument (which
            is passed as a positional argument) and the current loop variable values as the
            remaining arguments (which are passed as keyword arguments). Must return an
            iterable.

        num_iterations : NumIterationsSpecifier
            Specifier for the number of iterations associated with each combination of loop
            variable values.

        Returns
        -------
        Iterable
            The concatenation of the iterables obtained from all invocations of `f_callback`.
        """
        for loop_var_values, num_items in self.iter_loop_var_combinations_with_num_items_per_loop_iteration(
            num_items_per_loop_iteration, advance_loop_vars=advance_loop_vars
        ):
            yield from f_callback(num_items, **loop_var_values)

    def iter_loop_var_combinations_with_num_items_per_loop_iteration(
        self, num_items_per_loop_iteration: NumIterationsSpecifier, advance_loop_vars: bool = False
    ):
        num_items_per_loop_iteration = make_num_iterations_specifier(num_items_per_loop_iteration)
        for loop_var_vals in self.iter_loop_var_combinations(advance_loop_vars=advance_loop_vars):
            logger.debug(f"[EEE] {self.loop_variables[0]}, {self.loop_variables[0].cur_value}")
            yield loop_var_vals, num_items_per_loop_iteration(**loop_var_vals)

    # def iter_loop_var_combinations(self, var_names=None):
    def iter_loop_var_combinations(self, advance_loop_vars=False):
        """
        Return all combinations of values of the loop variables present in this
        loop runner (or of the loop variables in `var_names` if specified).

        Returns
        -------
        Iterable
            Iterable containing all possible combinations of loop variable values.
        """
        if advance_loop_vars:
            self.rewind_all_loop_variables()

        value_combinations_per_level = (
            StatefulZip(
                *(
                    loop_var.iter_values_and_optionally_advance(advance=advance_loop_vars)
                    for loop_var in self.loop_variables_by_level[level]
                )
            )
            for level in reversed(sorted(self.loop_variables_by_level.keys()))
        )

        for val_combs in product_of_iterables(*value_combinations_per_level):
            yield dict(concatenate_tuples(val_combs))
