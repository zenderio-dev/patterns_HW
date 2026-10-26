from datetime import datetime
from Src.Core.abstract_convert_factory import abstract_convert_factory
from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.abstract_model import abstract_model
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor

"""
Фабрика конвертеров. Подбирает конвертер по типу значения
"""
class convert_factory(abstract_convert_factory):
    __mapping: dict = None

    """
    Создать фабрику: сопоставление типа значения и конвертера
    """
    def __init__(self):
        basic = basic_convertor()
        reference = reference_convertor(self)
        self.__mapping = {
            int: basic,
            float: basic,
            str: basic,
            type(None): basic,
            datetime: datetime_convertor(),
            abstract_model: reference,
            list: reference,
            tuple: reference,
            dict: reference,
        }

    """
    Подобрать конвертер по типу значения или ближайшему базовому типу.
    Для неподдерживаемого типа - None
    """
    def create(self, value) -> abstract_convertor:
        return next((self.__mapping[value_type] for value_type in type(value).__mro__
                     if value_type in self.__mapping), None)
