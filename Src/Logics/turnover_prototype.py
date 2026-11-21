from decimal import Decimal

from Src.Core.validator import validator
from Src.Dtos.filter_dto import filter_dto
from Src.Logics.filter_prototype import filter_prototype
from Src.Models.transaction_model import transaction_model


class turnover_prototype(filter_prototype):
    """Прототип ОСВ по отфильтрованным движениям за период."""

    def __init__(self, source):
        """Принять движения и установить открытый период."""
        super().__init__(source)
        for item in self.data:
            validator.validate(item, transaction_model)
        self.__date_from = None
        self.__date_to = None

    def clone(self, condition: filter_dto) -> 'turnover_prototype':
        """Склонировать отбор и уточнить период, сохраняя тип прототипа."""
        result = super().clone(condition)
        result.__date_from = condition.date_from or self.__date_from
        result.__date_to = condition.date_to or self.__date_to
        filter_dto(date_from=result.__date_from, date_to=result.__date_to)
        return result

    def build(self) -> list:
        """Сложить начальные остатки и обороты в базовых единицах."""
        rows = {}
        for movement in self.data:
            if self.__date_to is not None and movement.date > self.__date_to:
                continue
            key = movement.storage.unique_code, movement.nomenclature.unique_code
            if key not in rows:
                unit = movement.base_unit()
                rows[key] = {
                    "storage_code": movement.storage.unique_code,
                    "storage_name": movement.storage.name,
                    "nomenclature_code": movement.nomenclature.unique_code,
                    "nomenclature_name": movement.nomenclature.name,
                    "range_code": unit.unique_code,
                    "range_name": unit.name,
                    "opening": Decimal(0), "income": Decimal(0), "expense": Decimal(0),
                }
            row = rows[key]
            amount = movement.base_value()
            if self.__date_from is not None and movement.date < self.__date_from:
                row["opening"] += amount
            elif amount > 0:
                row["income"] += amount
            else:
                row["expense"] -= amount

        for row in rows.values():
            row["closing"] = row["opening"] + row["income"] - row["expense"]
            for field in ("opening", "income", "expense", "closing"):
                row[field] = float(row[field])
        return list(rows.values())
