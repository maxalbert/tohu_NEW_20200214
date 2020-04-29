import pandas as pd
from random import Random
from .base import TohuBaseGenerator
from .timestamp_helpers import normalise_start_and_stop_timestamps_from_optional_start_stop_and_date

__all__ = ["Timestamp"]


class Timestamp(TohuBaseGenerator):
    def __init__(self, *, start=None, stop=None, date=None):
        super().__init__()
        self.start, self.stop = normalise_start_and_stop_timestamps_from_optional_start_stop_and_date(start, stop, date)
        self.timedelta_seconds = (self.stop - self.start).total_seconds()
        self.randgen = Random()

    def __next__(self):
        seconds_after_start = self.randgen.randint(0, self.timedelta_seconds)
        return self.start + pd.Timedelta(seconds_after_start, unit="s")

    def reset(self, seed=None):
        super().reset(seed)
        self.randgen.seed(seed)

    def spawn(self, gen_mapping=None):
        new_gen = Timestamp(start=self.start, stop=self.stop)
        new_gen._set_state_from(self)
        return new_gen

    def _set_state_from(self, other):
        super()._set_state_from(other)
        self.randgen.setstate(other.randgen.getstate())
