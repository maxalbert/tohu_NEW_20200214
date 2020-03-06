from abc import ABCMeta
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


def augment_init_method(cls):
    """
    Replace the existing cls.__init__() method with a new one which
    also initialises the field generators and similar bookkeeping.
    """

    orig_init = cls.__init__

    def new_init(self, *args, **kwargs):
        self._tohu_init_args = args
        self._tohu_init_kwargs = kwargs
        orig_init(self, *args, **kwargs)

        # After the original __init__() method, call CustomGenerator.__init__() in
        # order to build up the tohu_namespace with the constituent generators, etc.
        super(cls, self).__init__()  # TODO: does this behave correctly with longer inheritance chains? I think so...(?)

    cls.__init__ = new_init


class CustomGeneratorMeta(ABCMeta):
    def __new__(metacls, cg_name, bases, clsdict):
        # Create new custom generator class
        new_cls = super(CustomGeneratorMeta, metacls).__new__(metacls, cg_name, bases, clsdict)

        # Augment original init method with bookkeeping needed for custom generators
        # (but only
        if new_cls._is_proper_custom_generator_subclass():
            augment_init_method(new_cls)

        return new_cls


class CustomGenerator(TohuBaseGenerator, metaclass=CustomGeneratorMeta):
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
        self.__dict__.update(self._tohu_namespace.field_generators)

    @classmethod
    def _is_proper_custom_generator_subclass(cls):
        try:
            return cls is not CustomGenerator
        except NameError:
            # This can happen inside CustomGeneratorMeta above while
            # the CustomGenerator class itself is being created, so
            # that the `CustomGenerator` symbol doesn't exist yet.
            return False

    def spawn(self, gen_mapping=None):
        # Note: the attributes _tohu_init_args and _tohu_init_kwargs are set in
        # the custom generator metaclass (in the augmented __init__() method).
        return self.__class__(*self._tohu_init_args, **self._tohu_init_kwargs)

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
