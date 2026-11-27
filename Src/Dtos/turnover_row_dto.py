from dataclasses import dataclass
from decimal import Decimal


@dataclass
class turnover_row_dto:
    """Строка ОСВ по складу и номенклатуре в базовой единице."""

    storage_code: str
    storage_name: str
    nomenclature_code: str
    nomenclature_name: str
    range_code: str
    range_name: str
    opening: Decimal = Decimal(0)
    income: Decimal = Decimal(0)
    expense: Decimal = Decimal(0)
    closing: Decimal = Decimal(0)
