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

    def missing_init_method(*args, **kwargs):
        return

    # Store the original __init__() method so that we can call it
    # from the augmented one below. However, only do this if the user
    # explicitly defined __init__() on the class `cls`, otherwise we'd
    # set orig_init = CustomGenerator.__init__ and we would end  up
    # calling it twice - once through `orig_init(self, *args, **kwargs)`
    # and a second time through `super(cls, self).__init__()`.
    if cls.__init__ is not CustomGenerator.__init__:
        # If the user defined a custom __init__ method on the class `cls`,
        # store the original __init__ method so that we can call it from
        # the augmented method `new_init` defined below.
        orig_init = cls.__init__
    else:
        # The user didn't explicitly define __init__ on the class `cls`,
        # so we replace it with a no-op placeholder (otherwise we'd end
        # up calling CustomGenerator.__init__ twice).
        orig_init = missing_init_method

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

        # Update the instance dict so that the user can access the
        # custom generator's constituent generators directly via
        # instance attributes if needed.
        #
        # Note that we also make the 'hidden' generators accessible
        # via instance attributes. They are only hidden in the sense
        # that the values produced by them won't be exported as fields
        # on the generated output items.
        self.__dict__.update(self._tohu_namespace.field_generators)
        self.__dict__.update(self._tohu_namespace.hidden_generators)

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

    def generate(self, num, *, seed=None):
        return ItemList(self.generate_as_list(num, seed=seed), self._tohu_namespace.tohu_items_class)

    def assign_loop_variable_values(self, name, values):
        self._tohu_namespace.assign_loop_variable_values(name, values)
