from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.abstract_model import abstract_model
from Src.Core.common import common
from Src.Core.validator import argument_exception

"""
Конвертер ссылок на модели и списков: вложенные объекты конвертируются фабрикой
"""
class reference_convertor(abstract_convertor):
    __factory = None

    """
    Создать конвертер с фабрикой для вложенных объектов
    """
    def __init__(self, factory):
        if factory is None:
            raise argument_exception("factory", "Не передана фабрика конвертеров")
        self.__factory = factory

    """
    Сформировать словарь по полям-ссылкам и полям-спискам
    """
    def convert(self, source) -> dict:
        result = {}
        for field in common.get_fields(source):
            value = getattr(source, field)
            if isinstance(value, (abstract_model, list, tuple)):
                result[field] = self.__factory.convert(value)
        return result
