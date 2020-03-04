from .base import TohuBaseGenerator


class LoopVariable(TohuBaseGenerator):
    def __init__(self, name, values):
        super().__init__()
        self.name = name
        self.values = values
        self.idx = 0
        self.cur_value = self.values[0]

    def __next__(self):
        return self.cur_value

    def reset(self, seed=None):
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
