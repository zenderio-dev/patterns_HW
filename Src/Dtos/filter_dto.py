from datetime import date

from Src.Core.validator import validator, argument_exception
from Src.Dtos.filter_type_enum import filter_type_enum


class filter_dto:
    """Условие отбора по строковому полю и необязательный период ОСВ."""

    def __init__(self, field: str = None, operation: filter_type_enum = filter_type_enum.EQUALS,
                 value: str = None, date_from: date = None, date_to: date = None):
        """Проверить условие фильтра и границы периода."""
        validator.validate(operation, filter_type_enum)
        if field is not None:
            validator.validate(field, str)
            parts = field.split(".")
            if parts[-1] not in ("name", "unique_code") or any(
                not part.isidentifier() or part.startswith("_") for part in parts
            ):
                raise argument_exception("field", "Допустим путь к name или unique_code")
            if not isinstance(value, str):
                raise argument_exception("value", "Значение фильтра должно быть строкой")
        elif value is not None:
            raise argument_exception("field", "Для значения нужно указать поле")
        for boundary in (date_from, date_to):
            if boundary is not None and type(boundary) is not date:
                raise argument_exception("period", "Граница периода должна быть датой")
        if date_from is not None and date_to is not None and date_from > date_to:
            raise argument_exception("period", "Начало периода позже окончания")
        self.__field = field
        self.__operation = operation
        self.__value = value
        self.__date_from = date_from
        self.__date_to = date_to

    @classmethod
    def from_dict(cls, source: dict) -> 'filter_dto':
        """Разобрать JSON-условие с датами в формате ГГГГ-ММ-ДД."""
        validator.validate(source, dict)
        if source.keys() - {"field", "operation", "value", "date_from", "date_to"}:
            raise argument_exception("source", "Неизвестное поле фильтра")
        try:
            operation = filter_type_enum(source.get("operation", "EQUALS"))
            dates = {}
            for field in ("date_from", "date_to"):
                value = source.get(field)
                if value is not None:
                    validator.validate(value, str)
                    dates[field] = date.fromisoformat(value)
        except (ValueError, TypeError) as ex:
            raise argument_exception("source", "Некорректная операция или дата") from ex
        return cls(source.get("field"), operation, source.get("value"), **dates)

    @property
    def field(self) -> str:
        """Путь к полю, отсутствие пути означает весь набор."""
        return self.__field

    @property
    def operation(self) -> filter_type_enum:
        """Операция сравнения."""
        return self.__operation

    @property
    def value(self) -> str:
        """Искомая строка."""
        return self.__value

    @property
    def date_from(self) -> date:
        """Первый день периода ОСВ."""
        return self.__date_from

    @property
    def date_to(self) -> date:
        """Последний день периода ОСВ включительно."""
        return self.__date_to
