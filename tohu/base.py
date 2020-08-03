import hashlib

from abc import abstractmethod
from itertools import islice
from tqdm import tqdm

__all__ = ["is_tohu_generator", "TohuBaseGenerator"]


def is_tohu_generator(g):
    """
    Helper function which returns True if `g` is a tohu generator and False otherwise.
    """
    return isinstance(g, TohuBaseGenerator)


class TohuBaseGenerator:
    """
    Base class for all of tohu's generators.
    """

    def __init__(self):
        self.tohu_name = None
        self.clones = []
        self.parent = None  # this will only be set for cloned generators to point to their parents
        self.is_hidden = False  # this is used for loop variables

    def __repr__(self):
        clsname = self.__class__.__name__
        name = "" if self.tohu_name is None else f"{self.tohu_name}: "
        return f"<{name}{clsname} (id={self.tohu_id})>"

    def __format__(self, format_specifier):
        clsname = self.__class__.__name__
        name = "" if self.tohu_name is None else f"{self.tohu_name}: "
        clone_info = "" if self.parent is None or format_specifier != "debug" else f" (clone of {self.parent})"
        return f"<{name}{clsname} (id={self.tohu_id}){clone_info}>"

    def __iter__(self):
        return self

    def set_tohu_name(self, tohu_name):
        """
        Set this generator's `tohu_name` attribute.

        This is mainly useful for debugging where one can temporarily
        use this at the end of generator definitions to set a name
        that will be displayed in debugging messages. For example:

            g1 = SomeGeneratorClass().set_tohu_name('g1')
            g2 = SomeGeneratorClass().set_tohu_name('g2')
        """
        self.tohu_name = tohu_name
        return self

    @property
    def tohu_id(self):
        """
        Return (truncated) md5 hash representing this generator.
        We truncate the hash simply for readability, as this is
        purely intended for debugging purposes and the risk of
        any collisions will be negligible.
        """
        myhash = hashlib.md5(str(id(self)).encode()).hexdigest()
        return myhash[:6]

    @abstractmethod
    def spawn(self, gen_mapping=None):  # pragma: no cover
        raise NotImplementedError(f"Class {self.__class__.__name__} does not implement method 'spawn'.")

    def _set_state_from(self, other):
        self.tohu_name = other.tohu_name

    def clone(self):
        new_gen = self.spawn(gen_mapping=None)
        self.clones.append(new_gen)
        new_gen.parent = self
        return new_gen

    def is_clone_of(self, other):
        return self.parent is other

    def reset(self, seed):
        for c in self.clones:
            c.reset(seed)
        return self

    def generate_as_stream(self, num, *, seed=None, progressbar=False):
        """
        Return sequence of `num` elements.

        If `seed` is not None, the generator is reset
        using this seed before generating the elements.
        """
        if seed is not None:
            self.reset(seed)

        items = islice(self, num)
        if progressbar:  # pragma: no cover
            items = tqdm(items, total=num)

        yield from items

    def generate_as_list(self, num, *, seed=None, progressbar=False):
        return list(self.generate_as_stream(num, seed=seed, progressbar=progressbar))
