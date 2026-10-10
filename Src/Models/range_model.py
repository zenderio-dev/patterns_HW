from Src.Core.entity_model import entity_model
from Src.Core.validator import validator, argument_exception

"""
Модель единицы измерения
"""
class range_model(entity_model):
    __value:int = 1
    __base:'range_model' = None

    """
    Значение коэффициента пересчета
    """
    @property
    def value(self) -> int:
        return self.__value
    
    @value.setter
    def value(self, value: int):
        validator.validate(value, int)
        if value <= 0:
             raise argument_exception("Некорректный аргумент!")
        self.__value = value


    """
    Базовая единица измерения
    """
    @property
    def base(self):
        return self.__base
    
    @base.setter
    def base(self, value):
        self.__base = value


    """
    Фабричный метод. Базовая единица измерения «грамм»
    """
    @staticmethod
    def create_gram() -> 'range_model':
        result = range_model()
        result.name = "грамм"
        return result

    """
    Фабричный метод. Единица измерения «кг» = 1000 грамм.
    base - готовый «грамм», если не передан - создаётся новый
    """
    @staticmethod
    def create_kilogram(base: 'range_model' = None) -> 'range_model':
        result = range_model()
        result.name = "кг"
        result.value = 1000
        result.base = base if base is not None else range_model.create_gram()
        return result

    """
    Фабричный метод. Единица измерения «штука»
    """
    @staticmethod
    def create_piece() -> 'range_model':
        result = range_model()
        result.name = "штука"
        return result
