from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.abstract_convert_factory import abstract_convert_factory
from Src.Core.common import common
from Src.Core.validator import validator, argument_exception

"""
Конвертер ссылок: формирует словарь по всем полям объекта.
Простые поля и даты конвертирует подобранный фабрикой конвертер,
ссылки на модели, списки и словари разворачиваются во вложенные словари
"""
class reference_convertor(abstract_convertor):
    __factory: abstract_convert_factory = None

    """
    Создать конвертер с фабрикой для подбора конвертеров полей
    """
    def __init__(self, factory: abstract_convert_factory):
        self.factory = factory

    """
    Фабрика конвертеров
    """
    @property
    def factory(self) -> abstract_convert_factory:
        return self.__factory

    @factory.setter
    def factory(self, value: abstract_convert_factory):
        validator.validate(value, abstract_convert_factory)
        self.__factory = value

    """
    Сформировать словарь по объекту или словарю
    """
    def convert(self, source) -> dict:
        if source is None:
            raise argument_exception("source", "Не передан объект для конвертации")
        if isinstance(source, dict):
            return {str(key): self.__convert_value(value) for key, value in source.items()}

        result = {}
        converted = {}
        for field in common.get_fields(source):
            value = getattr(source, field)
            convertor = self.__factory.create(value)
            if isinstance(convertor, reference_convertor):
                result[field] = self.__convert_value(value)
            elif convertor is not None:
                if convertor not in converted:
                    converted[convertor] = convertor.convert(source)
                result[field] = converted[convertor][field]
        return result

    """
    Сконвертировать значение-ссылку: список - список, модель или словарь - словарь,
    простое значение внутри списка остается как есть
    """
    def __convert_value(self, value):
        if isinstance(value, (list, tuple)):
            return [self.__convert_value(item) for item in value]
        if isinstance(self.__factory.create(value), reference_convertor):
            return self.convert(value)
        return value
