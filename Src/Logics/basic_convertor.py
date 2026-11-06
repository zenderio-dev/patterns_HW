from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.common import common
from Src.Core.validator import argument_exception

"""
Конвертер полей простых типов: числа, строки и пустые значения
"""
class basic_convertor(abstract_convertor):

    """
    Сформировать словарь по полям простых типов
    """
    def convert(self, source) -> dict:
        if source is None:
            raise argument_exception("source", "Не передан объект для конвертации")
        result = {}
        for field in common.get_fields(source):
            value = getattr(source, field)
            if value is None or isinstance(value, (int, float, str)):
                result[field] = value
        return result
