from Src.Core.validator import validator

"""
Результат формирования отчета: текст или бинарные данные
"""
class report_result_dto:
    __text: str = ""
    __binary: bytes = b""

    """
    Текстовый результат
    """
    @property
    def text(self) -> str:
        return self.__text

    @text.setter
    def text(self, value: str):
        validator.validate(value, str)
        self.__text = value
        self.__binary = b""

    """
    Бинарный результат
    """
    @property
    def binary(self) -> bytes:
        return self.__binary

    @binary.setter
    def binary(self, value: bytes):
        validator.validate(value, bytes)
        self.__binary = value
        self.__text = ""
