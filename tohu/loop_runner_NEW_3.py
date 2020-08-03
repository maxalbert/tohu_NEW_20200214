import itertools
from typing import Callable, List, Optional
from tohu.seed_generator import SeedGenerator
from .num_iterations_specifier import make_num_iterations_specifier, NumIterationsSpecifier


def concatenate_tuples(list_of_tuples):
    """
    Helper function to combine multiple tuples into a single one.
    """
    return sum(list_of_tuples, ())


def unique_values(iterable):
    seen = set()
    for vals_dict in iterable:
        vals_tuple = tuple(vals_dict.items())
        if vals_tuple not in seen:
            seen.add(vals_tuple)
            yield vals_dict


def make_filtered_callback(g, loop_var_vals_to_filter):
    def f_callback_filtered(cur_loop_var_values, num_items, cur_seed):
        vals_subset = {name: val for (name, val) in cur_loop_var_values.items() if name in loop_var_vals_to_filter}
        if tuple(vals_subset.items()) == tuple(loop_var_vals_to_filter.items()):
            g.reset(cur_seed)
            yield from g.generate_as_stream(num=num_items)
        else:
            return []

    return f_callback_filtered


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
                       f_callback(loop_var_values, num_iterations, current_seed)

    Note that the above loop structure is slightly simplified because we allow
    iterating over multiple loop variables simultaneously at the same level. So
    any of the lines

       for x_i in values_i:

    can be replaced with the following more general one:

       for (x_i, y_i, ...) in zip(values_x_i, values_y_i, ...)

    Note that the implementation of the this class assumes that there are
    only comparatively few loop variable value combinations to cycle through
    and that the bulk of the work happens inside f_callback in the innermost
    part of the loop. If this assumption does not hold execution may not be
    very efficient.
    """

    def __init__(self):
        self.loop_variables_by_level = {}
        self.loop_variables_by_name = {}

    def add_loop_variables_at_level(self, loop_vars, *, level):
        assert isinstance(loop_vars, dict)
        self.loop_variables_by_level[level] = [x.set_loop_level(level) for x in loop_vars.values()]
        # TODO: check none of the new names exist yet!
        self.loop_variables_by_name.update(loop_vars)

    def print_current_loop_var_values(self):
        """
        Helper function which displays the current values of the loop variables in this loop runner
        (useful for debugging).
        """
        print({x.name: x.cur_value for x in self.loop_variables})

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
        def f_callback(cur_loop_var_values, num_items, cur_seed):
            g.reset(cur_seed)
            yield from g.generate_as_list(num=num_items)

        yield from self.iter_loop_var_combinations_with_callback(
            f_callback, num_items_per_loop_cycle, seed=seed, advance_loop_vars=True
        )

    def produce_items_from_tohu_generator_for_loop_var_subset(
        self, g, num_items_per_loop_cycle, loop_var_subset, seed=None
    ):
        for cur_vals in self.iter_loop_var_combinations(var_names=loop_var_subset):
            f_callback_filtered = make_filtered_callback(g, cur_vals)
            yield cur_vals, self.iter_loop_var_combinations_with_callback(
                f_callback_filtered, num_items_per_loop_cycle, seed=seed, advance_loop_vars=True
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
              - the current loop variable values (passed as a dictionary of name-value pairs)
              - the current number of iterations
              - the current seed
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

            yield from f_callback(loop_var_values, num_items, cur_seed)

    def iter_loop_var_combinations_with_num_ticks_and_seed_for_each_loop_cycle(
        self, num_ticks_per_loop_cycle: NumIterationsSpecifier, initial_seed: Optional[int]
    ):
        num_ticks_per_loop_cycle = make_num_iterations_specifier(num_ticks_per_loop_cycle)

        seed_generator = SeedGenerator()
        seed_generator.reset(initial_seed)

        for cur_vals in self.iter_loop_var_combinations():
            # TODO: have a think about whether we should construct a more specific seed for
            #       each loop cycle that incorporates the current loop variable values.
            cur_seed = next(seed_generator)
            yield cur_vals, num_ticks_per_loop_cycle(**cur_vals), cur_seed

    def iter_loop_var_combinations(self, var_names: Optional[List[str]] = None):
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

        if var_names is None:
            for val_comb in itertools.product(*value_combinations_per_level):
                yield dict(concatenate_tuples(val_comb))
        else:

            # Here we ensure that `var_names` is ordered in the same way as the
            # loop variables in this loop runner, to ensure that `vals_subset`
            # is extracted correctly below.
            #
            # TODO: have a think whether the order of names in `var_names`
            #       should influence th order of the returned result or not.
            loop_var_names_ordered_by_level = sum(
                [[x.name for x in vars] for vars in reversed(self.loop_variables_by_level.values())], []
            )
            var_names_ordered = [name for name in loop_var_names_ordered_by_level if name in var_names]

            def get_val_comb_for_subset(vals):
                vals = dict(concatenate_tuples(vals))
                vals_subset = {name: vals[name] for name in var_names_ordered}
                return vals_subset

            yield from (
                unique_values(get_val_comb_for_subset(x) for x in itertools.product(*value_combinations_per_level))
            )

    def get_total_number_of_ticks(self, *, num_ticks_per_loop_cycle):
        num_ticks_for_individual_loop_cycles = [
            num
            for _, num, _ in self.iter_loop_var_combinations_with_num_ticks_and_seed_for_each_loop_cycle(
                num_ticks_per_loop_cycle=num_ticks_per_loop_cycle, initial_seed=None
            )
        ]
        return sum(num_ticks_for_individual_loop_cycles)
