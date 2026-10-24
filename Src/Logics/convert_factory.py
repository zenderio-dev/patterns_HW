from datetime import datetime
from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.abstract_model import abstract_model
from Src.Core.common import common
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor

"""
Фабрика конвертеров. Выбирает конвертер по типу значения
и формирует по любому объекту набор словарей согласно его структуре
"""
class convert_factory:
    __basic: basic_convertor = None
    __datetime: datetime_convertor = None
    __reference: reference_convertor = None

    """
    Создать фабрику с конвертерами
    """
    def __init__(self):
        self.__basic = basic_convertor()
        self.__datetime = datetime_convertor()
        self.__reference = reference_convertor(self)

    """
    Выбрать конвертер по типу значения. Для неподдерживаемого типа - None
    """
    def create(self, value) -> abstract_convertor:
        if value is None or isinstance(value, (int, float, str)):
            return self.__basic
        if isinstance(value, datetime):
            return self.__datetime
        if isinstance(value, (abstract_model, list, tuple)):
            return self.__reference
        return None

    """
    Сконвертировать любой объект: простое значение - как есть, дата - строка ISO,
    список - список, объект - словарь по полям с помощью выбранных конвертеров
    """
    def convert(self, source):
        if source is None or isinstance(source, (int, float, str)):
            return source
        if isinstance(source, datetime):
            return source.isoformat()
        if isinstance(source, (list, tuple)):
            return [self.convert(item) for item in source]

        fields = common.get_fields(source)
        convertors = []
        for field in fields:
            convertor = self.create(getattr(source, field))
            if convertor is not None and convertor not in convertors:
                convertors.append(convertor)

        values = {}
        for convertor in convertors:
            values.update(convertor.convert(source))
        return {field: values[field] for field in fields if field in values}
