from Src.Core.abstract_model import abstract_model
from Src.Core.validator import validator, argument_exception
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model

"""
Модель строки технологической карты: ингредиент, его количество
и масса брутто / нетто в граммах
"""
class receipt_item_model(abstract_model):
    __nomenclature: nomenclature_model = None
    __range: range_model = None
    __quantity: float = 1
    __unit_weight: float = None
    __waste: float = 0

    """
    Проверить, что значение - число (bool не считается числом)
    """
    @staticmethod
    def __validate_number(value) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise argument_exception("value", "Значение должно быть числом")

    """
    Ингредиент (номенклатура)
    """
    @property
    def nomenclature(self) -> nomenclature_model:
        return self.__nomenclature

    @nomenclature.setter
    def nomenclature(self, value: nomenclature_model):
        validator.validate(value, nomenclature_model)
        self.__nomenclature = value

    """
    Единица измерения, в которой указано количество (грамм, штука и т.д.)
    """
    @property
    def range(self) -> range_model:
        return self.__range

    @range.setter
    def range(self, value: range_model):
        validator.validate(value, range_model)
        self.__range = value

    """
    Количество в единице измерения строки. Больше нуля
    """
    @property
    def quantity(self) -> float:
        return self.__quantity

    @quantity.setter
    def quantity(self, value: float):
        self.__validate_number(value)
        if value <= 0:
            raise argument_exception("quantity", "Количество должно быть больше нуля")
        self.__quantity = value

    """
    Масса одной единицы в граммах. Если не задана - коэффициент единицы
    измерения (грамм = 1, кг = 1000). Для штук задаётся явно
    """
    @property
    def unit_weight(self) -> float:
        if self.__unit_weight is not None:
            return self.__unit_weight
        return self.__range.value if self.__range is not None else 1

    @unit_weight.setter
    def unit_weight(self, value: float):
        self.__validate_number(value)
        if value <= 0:
            raise argument_exception("unit_weight", "Масса единицы должна быть больше нуля")
        self.__unit_weight = value

    """
    Процент отходов при холодной обработке (скорлупа, очистки). От 0 до 100
    """
    @property
    def waste(self) -> float:
        return self.__waste

    @waste.setter
    def waste(self, value: float):
        self.__validate_number(value)
        if value < 0 or value >= 100:
            raise argument_exception("waste", "Процент отходов должен быть от 0 до 100")
        self.__waste = value

    """
    Масса брутто, г - масса продукта до обработки
    """
    @property
    def brutto(self) -> float:
        return self.__quantity * self.unit_weight

    """
    Масса нетто, г - масса продукта после холодной обработки (за вычетом отходов)
    """
    @property
    def netto(self) -> float:
        return self.brutto * (100 - self.__waste) / 100

    """
    Фабричный метод. Строка технологической карты.
    unit_weight - масса одной единицы, г (для штук), waste - процент отходов
    """
    @staticmethod
    def create(nomenclature: nomenclature_model, range: range_model, quantity: float,
               unit_weight: float = None, waste: float = 0) -> 'receipt_item_model':
        result = receipt_item_model()
        result.nomenclature = nomenclature
        result.range = range
        result.quantity = quantity
        if unit_weight is not None:
            result.unit_weight = unit_weight
        result.waste = waste
        return result
