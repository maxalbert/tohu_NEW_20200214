from tohu.base import TohuBaseGenerator


class LoopVariableExhaustedNEW3(Exception):
    """
    Custom exception to indicate that a loop variable
    has iterated through all its values.
    """


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

    def update_current_value(self, value):
        if value not in self.values:
            raise ValueError(f"Invalid value for {self}: {value}")

        self.idx = self.values.index(value)
        self.cur_value = value

        for c in self.clones:
            c.update_current_value(value)

    def spawn(self, gen_mapping=None):
        return self.__class__(self.name, self.values).set_loop_level(self.loop_level)
