import re
from abc import ABCMeta
from functools import wraps
from .base import TohuBaseGenerator
from .item_list_lazy_NEW import LazyItemListNEW
from .tohu_namespace_NEW_3 import TohuNamespaceNEW3

__all__ = ["CustomGeneratorNEW3"]


def derive_tohu_items_class_name(custom_gen_class_name):
    m = re.match("^(.*)Generator$", custom_gen_class_name)
    if m is None:
        raise ValueError(
            f"Name of custom generator class must end with '[...]Generator', got: {custom_gen_class_name!r}"
        )
    return m.group(1)


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
    if cls.__init__ is not CustomGeneratorNEW3.__init__:
        # If the user defined a custom __init__ method on the class `cls`,
        # store the original __init__ method so that we can call it from
        # the augmented method `new_init` defined below.
        orig_init = cls.__init__
    else:
        # The user didn't explicitly define __init__ on the class `cls`,
        # so we replace it with a no-op placeholder (otherwise we'd end
        # up calling CustomGenerator.__init__ twice).
        orig_init = missing_init_method

    @wraps(orig_init)
    def new_init(self, *args, **kwargs):
        self._tohu_init_args = args
        self._tohu_init_kwargs = kwargs
        orig_init(self, *args, **kwargs)

        # After the original __init__() method, call CustomGenerator.__init__() in
        # order to build up the tohu_namespace with the constituent generators, etc.
        super(cls, self).__init__()  # TODO: does this behave correctly with longer inheritance chains? I think so...(?)

    cls.__init__ = new_init


class CustomGeneratorMetaNEW3(ABCMeta):
    def __new__(metacls, cg_name, bases, clsdict):
        # Create new custom generator class
        new_cls = super(CustomGeneratorMetaNEW3, metacls).__new__(metacls, cg_name, bases, clsdict)

        # The following are needed in the `@foreach` decorator
        # to keep track of loop variables.
        new_cls._tohu_cg_class_loop_variables = []

        # Augment original init method with bookkeeping needed for custom generators
        # (but only if the
        if new_cls._is_proper_custom_generator_subclass():
            augment_init_method(new_cls)

        return new_cls


class CustomGeneratorNEW3(TohuBaseGenerator, metaclass=CustomGeneratorMetaNEW3):
    _dependency_mapping_for_tohu_namespace = {}

    def __init__(self):
        super().__init__()

        # Create an empty tohu namespace, and register any pre-existing dependency mapping (for loop variables)
        self._tohu_namespace = TohuNamespaceNEW3(dependency_mapping=self._dependency_mapping_for_tohu_namespace)

        # Add remaining tohu generators present on the custom generator
        # class/instance to the tohu namespace.
        self._tohu_namespace.add_field_generators_from_dict(self.__class__.__dict__)
        self._tohu_namespace.add_field_generators_from_dict(self.__dict__)
        self.tohu_items_class_name = derive_tohu_items_class_name(self.__class__.__name__)
        self.__dict__.update(self._tohu_namespace.field_generators)

    @classmethod
    def _is_proper_custom_generator_subclass(cls):
        try:
            return cls is not CustomGeneratorNEW3
        except NameError:
            # This will happen inside CustomGeneratorMetaNEW above while
            # the CustomGeneratorNEW class itself is being created, so
            # that the `CustomGeneratorNEW` symbol doesn't exist yet.
            return False

    @classmethod
    def set_dependency_mapping_for_next_instance_creation(cls, dep_mapping):
        cls._dependency_mapping_for_tohu_namespace = dep_mapping

    def __next__(self):
        return next(self._tohu_namespace)

    def reset(self, seed):
        super().reset(seed)
        self._tohu_namespace.reset(seed)
        return self

    def generate(self, num, *, seed=None):
        return LazyItemListNEW(
            f_get_item_tuple_iterator=lambda: self.generate_as_stream(num, seed=seed),
            num_items=num,
            field_names=self._tohu_namespace.field_names,
            tohu_items_class_name=self.tohu_items_class_name,
        )
