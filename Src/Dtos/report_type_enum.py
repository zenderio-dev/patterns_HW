from enum import Enum

"""
Форматы отчетов
"""
class report_type_enum(Enum):
    CSV = 1
    MARKDOWN = 2
    XML = 3
    TXT = 4
    HTML = 5
