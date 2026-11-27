from dataclasses import dataclass
from datetime import date

from Src.Dtos.filter_type_enum import filter_type_enum


@dataclass(frozen=True)
class filter_dto:
    """Параметры строкового отбора и периода ОСВ."""

    field: str | None = None
    operation: filter_type_enum = filter_type_enum.EQUALS
    value: str | None = None
    date_from: date | None = None
    date_to: date | None = None
