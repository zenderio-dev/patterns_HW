from Src.Core.abstract_model import abstract_model
from Src.Core.validator import validator


"""
Общий класс для наследования. Содержит стандартное определение: код, наименование
"""
class entity_model(abstract_model):
    __name:str = ""

    """
    Наименование
    """
    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value:str):
        validator.validate(value, str)
        self.__name = value.strip()
