from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.common import common

"""
Конвертер полей простых типов: числа, строки и пустые значения
"""
class basic_convertor(abstract_convertor):

    """
    Сформировать словарь по полям простых типов
    """
    def convert(self, source) -> dict:
        result = {}
        for field in common.get_fields(source):
            value = getattr(source, field)
            if value is None or isinstance(value, (int, float, str)):
                result[field] = value
        return result
