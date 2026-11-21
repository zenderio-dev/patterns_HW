from Src.Core.abstract_manager import abstract_manager
from datetime import date
from Src.Core.validator import validator, operation_exception
from Src.Logics.settings_manager import settings_manager
from Src.Logics.storage_repository import storage_repository
from Src.Models.range_model import range_model
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.storage_model import storage_model
from Src.Models.receipt_model import receipt_model
from Src.Models.receipt_item_model import receipt_item_model
from Src.Models.transaction_model import transaction_model

"""
Менеджер хранилища (singleton). Хранит склады, единицы измерения, группы,
номенклатуру и технологические карты. При первом старте (settings.first_start) формирует первичные данные
"""
class storage_manager(abstract_manager):
    """Ключи справочников в хранилище"""
    range_key: str = "range"
    group_key: str = "group"
    nomenclature_key: str = "nomenclature"
    storage_key: str = "storage"
    receipt_key: str = "receipt"

    __data: dict = None
    __repository: storage_repository = None
    __transactions: tuple = ()
    __is_loaded: bool = False

    """Singleton. При первом старте формируются первичные данные"""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(storage_manager, cls).__new__(cls)
            cls.instance.load()
        return cls.instance

    """
    Сформировать первичные данные. Уже сформированные данные берутся из кэша.
    force = True - сформировать данные заново.
    Если это не первый старт - хранилище остаётся пустым
    """
    def load(self, file_name: str = "", force: bool = False) -> None:
        if self.__is_loaded and not force:
            return

        if not settings_manager().settings.first_start:
            self.__data = {key: [] for key in (self.range_key, self.group_key, self.nomenclature_key, self.storage_key, self.receipt_key)}
            self.__repository = storage_repository()
            self.__transactions = ()
            self.__is_loaded = False
            return

        self.__is_loaded = self.convert()

    """
    Сформировать первичные данные фабричными методами моделей:
    справочники и технологическую карту по рецепту Docs/Recipe.md
    """
    def convert(self) -> bool:
        gram = range_model.create_gram()
        kilogram = range_model.create_kilogram(gram)
        piece = range_model.create_piece()

        raw = group_model.create("Сырьё")
        packaging = group_model.create("Упаковка")

        flour = nomenclature_model.create("Пшеничная мука", raw, kilogram)
        cottage_cheese = nomenclature_model.create("Творог", raw, kilogram)
        sugar = nomenclature_model.create("Сахар", raw, kilogram)
        egg = nomenclature_model.create("Яйца", raw, piece)
        oil = nomenclature_model.create("Растительное масло", raw, kilogram)
        container = nomenclature_model.create("Контейнер для доставки", packaging, piece)

        storage = storage_model.create("Основной склад", "г. Иркутск, ул. Ленина, 1")

        # полуфабрикат ("блюдо в блюде") - входит в сырники
        dough = receipt_model.create("Творожное тесто", 4, 10)
        dough.add_item(receipt_item_model.create(cottage_cheese, gram, 400))
        dough.add_item(receipt_item_model.create(egg, piece, 1, unit_weight=50, waste=12))
        dough.add_item(receipt_item_model.create(flour, gram, 60))
        dough.add_item(receipt_item_model.create(sugar, gram, 40))
        for step in (
            "Разомните творог вилкой до однородности.",
            "Добавьте яйцо и сахар, перемешайте.",
            "Всыпьте муку и замесите мягкое тесто.",
        ):
            dough.add_step(step)

        receipt = receipt_model.create("Сырники", 4, 30)
        receipt.add_item(receipt_item_model.create_from_receipt(dough))
        receipt.add_item(receipt_item_model.create(oil, gram, 20))
        receipt.add_item(receipt_item_model.create(container, piece, 1, unit_weight=15))
        for step in (
            "Приготовьте творожное тесто.",
            "Сформируйте 8 сырников и обваляйте их в муке.",
            "Обжарьте на масле по 3-4 минуты с каждой стороны до золотистой корочки.",
            "Для доставки уложите сырники в контейнер и закройте крышкой.",
        ):
            receipt.add_step(step)

        data = {
            self.range_key: [gram, kilogram, piece],
            self.group_key: [raw, packaging],
            self.nomenclature_key: [flour, cottage_cheese, sugar, egg, oil, container],
            self.storage_key: [storage],
            self.receipt_key: [dough, receipt],
        }
        transactions = (
            transaction_model.create(flour, storage, kilogram, 1, date(2026, 1, 1)),
            transaction_model.create(flour, storage, kilogram, 2, date(2026, 1, 2)),
            transaction_model.create(flour, storage, gram, -500, date(2026, 1, 3)),
            transaction_model.create(flour, storage, kilogram, 9, date(2026, 1, 4)),
        )
        repository = storage_repository()
        for items in data.values():
            repository.registry_range(items)
        repository.registry_range(list(transactions))
        self.__data = data
        self.__repository = repository
        self.__transactions = transactions
        return True

    """
    Список типов сущностей (ключей справочников)
    """
    def keys(self) -> list:
        return list(self.__data.keys())

    """
    Все модели справочника key
    """
    def get(self, key: str) -> list:
        validator.validate(key, str)
        if key not in self.__data:
            raise operation_exception(f"Неизвестный справочник: {key}")
        return self.__data[key]

    """
    Модель справочника key с уникальным кодом unique_code
    """
    def find(self, key: str, unique_code: str):
        items = self.get(key)
        model = self.repository.get(unique_code)
        if model in items:
            return model
        raise operation_exception(f"Не найдена модель {key} с кодом {unique_code}")

    @property
    def repository(self) -> storage_repository:
        """Индекс доменных объектов и счётчиков связей."""
        return self.__repository

    @property
    def transactions(self) -> tuple:
        """Движения для построения оборотно-сальдовой ведомости."""
        return self.__transactions

    """
    Данные хранилища: ключ справочника -> список моделей
    """
    @property
    def data(self) -> dict:
        return self.__data

    """
    Признак того, что данные сгенерированы
    """
    @property
    def is_loaded(self) -> bool:
        return self.__is_loaded
