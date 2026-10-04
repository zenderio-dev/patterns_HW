from Src.Core.abstract_manager import abstract_manager
from Src.Models.range_model import range_model
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.storage_model import storage_model

"""
Менеджер хранилища (singleton). Хранит склады, единицы измерения, группы
и номенклатуру. При первом старте формирует первичные данные
"""
class storage_manager(abstract_manager):
    """Ключи справочников в хранилище"""
    range_key: str = "range"
    group_key: str = "group"
    nomenclature_key: str = "nomenclature"
    storage_key: str = "storage"

    __source: dict = None
    __data: dict = None
    __is_loaded: bool = False

    """Singleton. При первом старте формируются первичные данные"""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(storage_manager, cls).__new__(cls)
            cls.instance.load()
        return cls.instance

    """
    Сформировать первичные данные справочников (ингредиенты рецепта Docs/Recipe.md)
    и преобразовать их в модели. Уже сформированные данные берутся из кэша.
    force = True - сформировать данные заново
    """
    def load(self, file_name: str = "", force: bool = False) -> None:
        if self.__is_loaded and not force:
            return

        self.__source = {
            self.range_key: [
                # наименование, коэффициент, базовая единица
                ("грамм", 1, None),
                ("кг", 1000, "грамм"),
                ("штука", 1, None),
            ],
            self.group_key: ["Сырьё"],
            self.nomenclature_key: [
                # наименование, группа, единица измерения
                ("Пшеничная мука", "Сырьё", "кг"),
                ("Сахар", "Сырьё", "кг"),
                ("Сливочное масло", "Сырьё", "кг"),
                ("Яйца", "Сырьё", "штука"),
                ("Ванилин", "Сырьё", "грамм"),
            ],
            self.storage_key: [
                # наименование, адрес
                ("Основной склад", "г. Иркутск, ул. Ленина, 1"),
            ],
        }
        self.__is_loaded = self.convert()

    """
    Преобразовать исходные данные в модели
    """
    def convert(self) -> bool:
        ranges = {}
        for name, value, base_name in self.__source[self.range_key]:
            item = range_model()
            item.name = name
            item.value = value
            item.base = ranges[base_name] if base_name else None
            ranges[name] = item

        groups = {}
        for name in self.__source[self.group_key]:
            item = group_model()
            item.name = name
            groups[name] = item

        nomenclatures = []
        for name, group_name, range_name in self.__source[self.nomenclature_key]:
            item = nomenclature_model()
            item.name = name
            item.group = groups[group_name]
            item.range = ranges[range_name]
            nomenclatures.append(item)

        storages = []
        for name, address in self.__source[self.storage_key]:
            item = storage_model()
            item.name = name
            item.address = address
            storages.append(item)

        self.__data = {
            self.range_key: list(ranges.values()),
            self.group_key: list(groups.values()),
            self.nomenclature_key: nomenclatures,
            self.storage_key: storages,
        }
        return True

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
