from Src.Core.entity_model import entity_model
from Src.Core.validator import validator, argument_exception
from Src.Models.receipt_item_model import receipt_item_model
from Src.Models.nomenclature_model import nomenclature_model

"""
Модель технологической карты (рецепта): состав, выход, описание процесса.
Корень агрегата - строки изменяются только через методы карты,
масса брутто / нетто вычисляется по строкам
"""
class receipt_model(entity_model):
    __portions: int = 1
    __cooking_time: int = 0
    __items: list = None
    __steps: list = None

    """
    Создать пустую технологическую карту
    """
    def __init__(self) -> None:
        super().__init__()
        self.__items = []
        self.__steps = []

    """
    Количество порций (выход)
    """
    @property
    def portions(self) -> int:
        return self.__portions

    @portions.setter
    def portions(self, value: int):
        validator.validate(value, int)
        if isinstance(value, bool) or value <= 0:
            raise argument_exception("portions", "Количество порций должно быть больше нуля")
        self.__portions = value

    """
    Время приготовления, мин
    """
    @property
    def cooking_time(self) -> int:
        return self.__cooking_time

    @cooking_time.setter
    def cooking_time(self, value: int):
        validator.validate(value, int)
        if isinstance(value, bool) or value <= 0:
            raise argument_exception("cooking_time", "Время приготовления должно быть больше нуля")
        self.__cooking_time = value

    """
    Строки технологической карты (только чтение)
    """
    @property
    def items(self) -> tuple:
        return tuple(self.__items)

    """
    Добавить строку. Один ингредиент может входить в карту только один раз
    """
    def add_item(self, item: receipt_item_model) -> None:
        validator.validate(item, receipt_item_model)
        if any(row.nomenclature == item.nomenclature for row in self.__items):
            raise argument_exception("item", "Ингредиент уже есть в технологической карте")
        self.__items.append(item)

    """
    Исключить из карты строку с ингредиентом nomenclature
    """
    def remove_item(self, nomenclature: nomenclature_model) -> None:
        validator.validate(nomenclature, nomenclature_model)
        for row in self.__items:
            if row.nomenclature == nomenclature:
                self.__items.remove(row)
                return
        raise argument_exception("nomenclature", "Ингредиента нет в технологической карте")

    """
    Шаги приготовления (только чтение)
    """
    @property
    def steps(self) -> tuple:
        return tuple(self.__steps)

    """
    Добавить шаг приготовления
    """
    def add_step(self, step: str) -> None:
        validator.validate(step, str)
        self.__steps.append(step.strip())

    """
    Масса брутто всей карты, г
    """
    @property
    def brutto(self) -> float:
        return sum(item.brutto for item in self.__items)

    """
    Масса нетто всей карты, г
    """
    @property
    def netto(self) -> float:
        return sum(item.netto for item in self.__items)

    """
    Фабричный метод. Пустая технологическая карта с наименованием,
    количеством порций и временем приготовления (мин)
    """
    @staticmethod
    def create(name: str, portions: int, cooking_time: int) -> 'receipt_model':
        result = receipt_model()
        result.name = name
        result.portions = portions
        result.cooking_time = cooking_time
        return result
