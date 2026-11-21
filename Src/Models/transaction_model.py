from datetime import date
from decimal import Decimal

from Src.Core.abstract_model import abstract_model
from Src.Core.validator import validator, argument_exception
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.storage_model import storage_model


class transaction_model(abstract_model):
    """Движение номенклатуры по складу, положительное для прихода."""

    @classmethod
    def from_dict(cls, source: dict) -> 'transaction_model':
        """Восстановить движение с подготовленными ссылками на модели."""
        movement_date = source.get("date")
        if isinstance(movement_date, str):
            try:
                movement_date = date.fromisoformat(movement_date)
            except ValueError as ex:
                raise argument_exception("date", "Некорректная дата движения") from ex
        result = cls.create(source.get("nomenclature"), source.get("storage"),
                            source.get("range"), source.get("value"), movement_date)
        result.unique_code = source.get("unique_code")
        return result

    @classmethod
    def create(cls, nomenclature: nomenclature_model, storage: storage_model,
               range: range_model, value: float, movement_date: date) -> 'transaction_model':
        """Создать проверенное движение в совместимой единице измерения."""
        result = cls()
        result.nomenclature = nomenclature
        result.storage = storage
        result.range = range
        result.value = value
        result.date = movement_date
        result.base_value()
        return result

    @property
    def nomenclature(self) -> nomenclature_model:
        """Номенклатура движения."""
        return self.__nomenclature

    @nomenclature.setter
    def nomenclature(self, value: nomenclature_model):
        """Проверить номенклатуру."""
        validator.validate(value, nomenclature_model)
        self.__nomenclature = value

    @property
    def storage(self) -> storage_model:
        """Склад движения."""
        return self.__storage

    @storage.setter
    def storage(self, value: storage_model):
        """Проверить склад."""
        validator.validate(value, storage_model)
        self.__storage = value

    @property
    def range(self) -> range_model:
        """Единица, в которой указано количество."""
        return self.__range

    @range.setter
    def range(self, value: range_model):
        """Проверить единицу измерения."""
        validator.validate(value, range_model)
        self.__range = value

    @property
    def value(self) -> float:
        """Приход со знаком плюс или расход со знаком минус."""
        return self.__value

    @value.setter
    def value(self, value: float):
        """Проверить конечное ненулевое количество."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise argument_exception("value", "Количество должно быть числом")
        if not Decimal(str(value)).is_finite() or value == 0:
            raise argument_exception("value", "Количество должно быть конечным и ненулевым")
        self.__value = value

    @property
    def date(self) -> date:
        """Дата проведения движения."""
        return self.__date

    @date.setter
    def date(self, value: date):
        """Принять календарную дату без времени."""
        if type(value) is not date:
            raise argument_exception("date", "Ожидается дата движения")
        self.__date = value

    def references(self) -> tuple:
        """Сущности, которые нельзя удалить при наличии движения."""
        return self.nomenclature, self.storage, self.range

    @staticmethod
    def __unit(unit: range_model) -> tuple:
        """Определить базовую единицу и коэффициент по всей цепочке."""
        factor = Decimal(1)
        visited = set()
        while unit.base is not None:
            if unit.unique_code in visited:
                raise argument_exception("range", "Циклическая цепочка единиц измерения")
            visited.add(unit.unique_code)
            factor *= unit.value
            unit = unit.base
        return unit, factor

    def base_unit(self) -> range_model:
        """Базовая единица для количества в ОСВ."""
        return self.__unit(self.range)[0]

    def base_value(self) -> Decimal:
        """Привести количество к базовой единице номенклатуры."""
        unit, factor = self.__unit(self.range)
        if unit != self.__unit(self.nomenclature.range)[0]:
            raise argument_exception("range", "Единица несовместима с номенклатурой")
        return Decimal(str(self.value)) * factor
