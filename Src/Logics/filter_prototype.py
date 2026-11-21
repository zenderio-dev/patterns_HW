from copy import copy

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
        result = copy(self)
        if condition.field is not None:
            result.__data = tuple(item for item in self.data if self.__matches(item, condition))
        return result

    def __matches(self, item, condition: filter_dto) -> bool:
        """Проверить наличие хотя бы одного подходящего значения по пути."""
        values = self.__values(item, condition.field.split("."))
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
