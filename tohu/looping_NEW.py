from .base import TohuBaseGenerator

__all__ = ["LoopVariableNEW"]


class LoopVariableExhaustedNEW(Exception):
    pass


class LoopVariableNEW(TohuBaseGenerator):
    def __init__(self, name, values):
        super().__init__()
        self.name = name
        self.values = values
        self.loop_level = None

        self.idx = 0
        self.cur_value = values[0]

    def __repr__(self):
        return f"<LoopVariable: name={self.name!r}, values={self.values!r}, loop_level={self.loop_level} (tohu_id={self.tohu_id})>"

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

    def reset_loop_variable(self):
        self.idx = 0
        self.cur_value = self.values[0]

        for c in self.clones:
            c.reset_loop_variable()

    def spawn(self, gen_mapping=None):
        return self.__class__(self.name, self.values).set_loop_level(self.loop_level)
