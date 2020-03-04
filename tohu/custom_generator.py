from .base import TohuBaseGenerator, SeedGenerator
from .item_list import ItemList
from .tohu_items_class import make_tohu_items_class, derive_tohu_items_class_name
from .tohu_namespace import TohuNamespace


def find_tohu_generators(x):
    """
    Find any attributes of the instance `x` or its class which are tohu generators.
    """
    class_candidates = list(x.__class__.__dict__.items())
    instance_candidates = list(x.__dict__.items())
    candidates = class_candidates + instance_candidates
    return {name: gen for (name, gen) in candidates if isinstance(gen, TohuBaseGenerator)}


class CustomGenerator(TohuBaseGenerator):
    """
    CustomGenerator allows combining other generators into a single entity.
    """

    loop_level = 0

    def __init__(self):
        super().__init__()
        self.seed_generator = SeedGenerator()

        tohu_items_class_name = derive_tohu_items_class_name(self.__class__.__name__)
        self._tohu_namespace = TohuNamespace(tohu_items_class_name)
        for name, gen in find_tohu_generators(self).items():
            self._tohu_namespace.add_generator(name, gen)
        self._tohu_namespace.make_tohu_items_class()

        # Update the instance dict so that the user can access
        # them directly via the instance attributes if needed.
        self.__dict__.update(self._tohu_namespace.generators)

    def __next__(self):
        return next(self._tohu_namespace)

    def reset(self, seed):
        # We construct a new internal seed by prepending the provided seed with
        # the class hierarchy of this generator. The purpoe of this is to avoid
        # a situation where two different custom generator classes contain
        # constituent generators of the same type (and at the same positions
        # in their definition). Otherwise this would lead to them producing the
        # same sequence of elements even though they live in two entirely unrelated
        # custom generators. While this isn't likely to ever be a problem in practice,
        # it can't do any harm to avoid it.
        str_class_hierarchy = ",".join([str(cls.__name__) for cls in self.__class__.__mro__])
        internal_seed = f"{str_class_hierarchy}{seed}"
        self._tohu_namespace.reset(internal_seed)

        return self

    @property
    def loop_variables(self):
        return self._tohu_namespace.loop_variables

    def advance_loop_variables(self):
        self._tohu_namespace.advance_loop_variables()

    def generate(self, num, *, seed=None):
        return ItemList(self.generate_as_list(num, seed=seed), self._tohu_namespace.tohu_items_class)
