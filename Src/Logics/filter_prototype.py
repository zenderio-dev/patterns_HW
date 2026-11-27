from copy import copy
from datetime import date

from Src.Core.abstract_prototype import abstract_prototype
from Src.Core.common import common
from Src.Core.validator import validator, argument_exception
from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.filter_type_enum import filter_type_enum


class filter_prototype(abstract_prototype):
    """Общий прототип фильтрации моделей, включая вложенные поля и списки."""

    def __init__(self, source):
        """Сохранить отдельный неизменяемый набор ссылок на исходные модели."""
        validator.validate(source, (list, tuple))
        self.__data = tuple(source)

    @property
    def data(self) -> tuple:
        """Результат отбора в исходном порядке."""
        return self.__data

    def clone(self, condition: filter_dto) -> 'filter_prototype':
        """Склонировать прототип и применить условие к его набору."""
        validator.validate(condition, filter_dto)
        validator.validate(condition.operation, filter_type_enum)
        result = copy(self)
        if condition.field is None:
            if condition.value is not None:
                raise argument_exception("field", "Для значения нужно указать поле")
            return result
        validator.validate(condition.field, str)
        if not isinstance(condition.value, str):
            raise argument_exception("value", "Значение фильтра должно быть строкой")
        path = condition.field.split(".")
        if path[-1] not in ("name", "unique_code") or any(
            not part.isidentifier() or part.startswith("_") for part in path
        ):
            raise argument_exception("field", "Допустим путь к name или unique_code")
        result.__data = tuple(item for item in self.data if self.__matches(item, condition, path))
        return result

    def clone_period(self, start: date = None, end: date = None, *,
                     include_end: bool = True) -> 'filter_prototype':
        """Отобрать движения по датам с включаемой или исключаемой верхней границей."""
        if any(bound is not None and type(bound) is not date for bound in (start, end)):
            raise argument_exception("period", "Граница периода должна быть датой")
        if start is not None and end is not None and start > end:
            raise argument_exception("period", "Начало периода позже окончания")
        result = copy(self)
        result.__data = tuple(item for item in self.data
                              if (start is None or item.date >= start)
                              and (end is None or item.date < end or (include_end and item.date == end)))
        return result

    def __matches(self, item, condition: filter_dto, path: list) -> bool:
        """Проверить наличие хотя бы одного подходящего значения по пути."""
        values = self.__values(item, path)
        if condition.operation == filter_type_enum.EQUALS:
            return any(value == condition.value for value in values)
        return any(condition.value.casefold() in value.casefold() for value in values)

    def __values(self, item, path: list) -> list:
        """Пройти по публичным свойствам, сохраняя путь при обходе списка."""
        if item is None:
            return []
        if isinstance(item, (list, tuple)):
            return [value for child in item for value in self.__values(child, path)]
        if not path:
            if not isinstance(item, str):
                raise argument_exception("field", "Поле фильтра должно быть строковым")
            return [item]
        if path[0] not in common.get_fields(item):
            raise argument_exception("field", f"Неизвестное поле: {path[0]}")
        return self.__values(getattr(item, path[0]), path[1:])
