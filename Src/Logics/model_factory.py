import inspect
from importlib import import_module
from pkgutil import walk_packages
import Src.Models
from Src.Core.abstract_model import abstract_model
from Src.Core.abstract_model_factory import abstract_model_factory
from Src.Core.validator import validator, argument_exception


"""
Фабрика моделей для восстановления данных хранилища
"""
class model_factory(abstract_model_factory):
    """
    Загрузить модули и собрать конкретные доменные классы с from_dict
    """
    def __init__(self):
        self.__models = {}
        for module_info in walk_packages(Src.Models.__path__, Src.Models.__name__ + "."):
            module = import_module(module_info.name)
            for _, model in inspect.getmembers(module, inspect.isclass):
                if (model.__module__ == module.__name__
                        and issubclass(model, abstract_model)
                        and not inspect.isabstract(model)
                        and callable(getattr(model, "from_dict", None))):
                    self.__models[model.__name__] = model

    """
    Выбрать класс из реестра и передать ему подготовленные поля
    """
    def create(self, model_type: str, source: dict) -> abstract_model:
        validator.validate(model_type, str)
        validator.validate(source, dict)
        if model_type not in self.__models:
            raise argument_exception("model_type", f"Неизвестный тип модели: {model_type}")
        model = self.__models[model_type]
        fields = {name for name, field in inspect.getmembers(model)
                  if isinstance(field, property)}
        if source.keys() - fields:
            raise argument_exception("source", "Неизвестное поле модели")
        return model.from_dict(source)
