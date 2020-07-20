import inspect

from .custom_generator_NEW_3 import CustomGeneratorNEW3
from .item_list_lazy_NEW import LazyItemListNEW
from .logging import logger
from .looping_NEW_3 import LoopRunnerNEW3


class LoopedCustomGeneratorInstance:
    def __init__(self, loop_runner, custom_gen_instance):
        self.loop_runner = loop_runner
        self.custom_gen_instance = custom_gen_instance

    def __repr__(self):
        return f"<{self.__class__.__name__} wrapping {self.custom_gen_instance}>"

    def generate_as_stream(self, *, num_items_per_loop_iteration, seed=None):
        logger.warning(
            "TODO: ensure that all loop variables have been assigned values (and perform any other sanity checks)!"
        )

        yield from self.loop_runner.produce_items_from_tohu_generator(
            self.custom_gen_instance, num_items_per_loop_iteration, seed
        )

    def generate(self, *, num_items_per_loop_iteration, seed=None):
        total_num_items = self.loop_runner.get_total_number_of_items(
            num_items_per_loop_iteration=num_items_per_loop_iteration
        )
        return LazyItemListNEW(
            f_get_item_tuple_stream_iterator=lambda: self.generate_as_stream(
                num_items_per_loop_iteration=num_items_per_loop_iteration, seed=seed
            ),
            num_items=total_num_items,
            field_names=self.custom_gen_instance._tohu_namespace.field_names,
            tohu_items_class_name=self.custom_gen_instance.tohu_items_class_name,
        )


class LoopedCustomGeneratorClass:
    def __init__(self, custom_gen_cls_or_looped_custom_gen_cls):
        if inspect.isclass(custom_gen_cls_or_looped_custom_gen_cls) and issubclass(
            custom_gen_cls_or_looped_custom_gen_cls, CustomGeneratorNEW3
        ):
            self.custom_gen_cls = custom_gen_cls_or_looped_custom_gen_cls
            self.loop_runner = LoopRunnerNEW3()
            self.cur_level = 0
        elif isinstance(custom_gen_cls_or_looped_custom_gen_cls, LoopedCustomGeneratorClass):
            self.custom_gen_cls = custom_gen_cls_or_looped_custom_gen_cls.custom_gen_cls
            self.loop_runner = custom_gen_cls_or_looped_custom_gen_cls.loop_runner
            self.cur_level = custom_gen_cls_or_looped_custom_gen_cls.cur_level
        else:
            raise TypeError(
                f"Cannot instantiate {self.__class__.__name__} with object of type {type(custom_gen_cls_or_looped_custom_gen_cls)}"
            )

    def __repr__(self):
        return f"<{self.__class__.__name__}: loop_vars={self.loop_runner.loop_variables}, cur_level={self.cur_level}>"

    def add_loop_variables_at_next_level_up(self, loop_vars):
        next_level_up = self.cur_level + 1
        self.loop_runner.add_loop_variables_at_level(loop_vars, level=next_level_up)
        self.cur_level = next_level_up

    def __call__(self, *args, **kwargs):
        loop_runner_spawned, loop_var_dep_mapping = self.loop_runner.spawn()
        logger.debug(f"loop_var_dep_mapping keys: {list(loop_var_dep_mapping.keys())}")
        self.custom_gen_cls.set_dependency_mapping_for_next_instance_creation(loop_var_dep_mapping)
        custom_gen_instance = self.custom_gen_cls(*args, **kwargs)
        return LoopedCustomGeneratorInstance(loop_runner_spawned, custom_gen_instance)
