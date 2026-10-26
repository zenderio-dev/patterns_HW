from datetime import datetime
from Src.Core.abstract_convertor import abstract_convertor
from Src.Core.common import common
from Src.Core.validator import argument_exception

"""
Конвертер полей с датой и временем
"""
class datetime_convertor(abstract_convertor):

    """
    Сформировать словарь по полям с датой: дата - строка в формате ISO
    """
    def convert(self, source) -> dict:
        if source is None:
            raise argument_exception("source", "Не передан объект для конвертации")
        result = {}
        for field in common.get_fields(source):
            value = getattr(source, field)
            if isinstance(value, datetime):
                result[field] = value.isoformat()
        return result
