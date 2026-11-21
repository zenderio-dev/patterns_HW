from enum import Enum


class filter_type_enum(Enum):
    """Способы сравнения строковых полей."""

    EQUALS = "EQUALS"
    LIKE = "LIKE"
