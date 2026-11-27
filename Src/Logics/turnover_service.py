from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.turnover_row_dto import turnover_row_dto
from Src.Logics.filter_prototype import filter_prototype
from Src.Logics.storage_manager import storage_manager
from Src.Models.transaction_model import transaction_model


class turnover_service:
    """Собирает оборотно-сальдовую ведомость по движениям из хранилища."""

    def __init__(self, storage: storage_manager):
        """Подключить источник движений."""
        self.__storage = storage

    def build(self, condition: filter_dto) -> list[turnover_row_dto]:
        """Отдельно выбрать начальные движения и обороты, затем объединить суммы."""
        source = filter_prototype(self.__storage.transactions)
        selected = source.clone(condition)
        rows = {}

        opening = ()
        if condition.date_from is not None:
            opening = selected.clone_period(end=condition.date_from, include_end=False).data
        for movement in opening:
            self.__row(rows, movement).opening += movement.base_value()

        turnover = selected.clone_period(start=condition.date_from, end=condition.date_to).data
        for movement in turnover:
            row = self.__row(rows, movement)
            amount = movement.base_value()
            if amount > 0:
                row.income += amount
            else:
                row.expense -= amount

        for row in rows.values():
            row.closing = row.opening + row.income - row.expense
        included = set(opening).union(turnover)
        keys = dict.fromkeys(self.__key(movement) for movement in selected.data if movement in included)
        return [rows[key] for key in keys]

    @staticmethod
    def __key(movement: transaction_model) -> tuple[str, str]:
        """Ключ строки по складу и номенклатуре движения."""
        return movement.storage.unique_code, movement.nomenclature.unique_code

    def __row(self, rows: dict, movement: transaction_model) -> turnover_row_dto:
        """Найти или создать строку для пары склада и номенклатуры."""
        storage = movement.storage
        nomenclature = movement.nomenclature
        key = self.__key(movement)
        if key not in rows:
            unit = movement.base_unit()
            rows[key] = turnover_row_dto(
                storage.unique_code, storage.name, nomenclature.unique_code,
                nomenclature.name, unit.unique_code, unit.name,
            )
        return rows[key]
