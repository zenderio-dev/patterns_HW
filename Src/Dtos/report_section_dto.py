from Src.Core.validator import validator

"""
Раздел отчета: наименование, заголовок и строки таблицы
"""
class report_section_dto:
    __name: str = ""
    __header: list = None
    __rows: list = None

    """
    Создать пустой раздел
    """
    def __init__(self):
        self.__header = []
        self.__rows = []

    """
    Наименование раздела
    """
    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str):
        validator.validate(value, str)
        self.__name = value

    """
    Заголовок: названия колонок
    """
    @property
    def header(self) -> list:
        return self.__header

    @header.setter
    def header(self, value: list):
        validator.validate(value, list)
        self.__header = value

    """
    Строки: список значений для каждой строки
    """
    @property
    def rows(self) -> list:
        return self.__rows

    @rows.setter
    def rows(self, value: list):
        validator.validate(value, list)
        self.__rows = value
