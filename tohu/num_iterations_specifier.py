from abc import ABCMeta
from typing import Callable, Sequence
from .logging import logger

__all__ = ["make_num_iterations_specifier", "NumIterationsSequenceExhausted"]


class NumIterationsSequenceExhausted(Exception):
    """
    Custom exception to indicate that a `num_iterations` sequence has been exhausted.
    """


class NumIterationsSpecifierBase(metaclass=ABCMeta):
    """
    Base class for the different classes representing num_iterations specifiers.
    """


class NumIterationsSpecifierFromCallable(NumIterationsSpecifierBase):
    def __init__(self, func_num_iterations: Callable):
        self.func_num_iterations = func_num_iterations

    def __call__(self, **kwargs):
        return self.func_num_iterations(**kwargs)


class NumIterationsSpecifierFromInt(NumIterationsSpecifierBase):
    def __init__(self, num_iterations: int):
        self.num_iterations = num_iterations

    def __call__(self, **kwargs):
        return self.num_iterations


class NumIterationsSpecifierFromSequence(NumIterationsSpecifierBase):
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
