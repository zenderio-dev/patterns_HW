from Src.Core.abstract_manager import abstract_manager
from threading import RLock
from uuid import uuid4
from Src.Core.abstract_model import abstract_model
from Src.Core.common import common
from Src.Core.validator import validator, operation_exception, argument_exception, conflict_exception
from Src.Logics.deserializer import deserializer
from Src.Logics.settings_manager import settings_manager
from Src.Models.range_model import range_model
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.storage_model import storage_model
from Src.Models.receipt_model import receipt_model
from Src.Models.receipt_item_model import receipt_item_model

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

    __models = {range_key: range_model, group_key: group_model,
                nomenclature_key: nomenclature_model, storage_key: storage_model,
                receipt_key: receipt_model}
    __lock = RLock()
    __data: dict = None
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

        self.__data = {
            self.range_key: [gram, kilogram, piece],
            self.group_key: [raw, packaging],
            self.nomenclature_key: [flour, cottage_cheese, sugar, egg, oil, container],
            self.storage_key: [storage],
            self.receipt_key: [dough, receipt],
        }
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
        for item in self.get(key):
            if item.unique_code == unique_code:
                return item
        raise operation_exception(f"Не найдена модель {key} с кодом {unique_code}")

    """Добавить проверенную сущность в справочник."""
    def create(self, key: str, source: dict) -> abstract_model:
        with self.__lock:
            collection = self.get(key)
            validator.validate(source, dict)
            model = self.__build_model(key, source, source.get("unique_code", uuid4().hex))
            self.__validate_change(model)
            collection.append(model)
            return model

    """Обновить переданные поля, сохранив объект для существующих ссылок."""
    def update(self, key: str, unique_code: str, source: dict) -> abstract_model:
        with self.__lock:
            current = self.find(key, unique_code)
            validator.validate(source, dict)
            fields = {name: getattr(current, name) for name in common.get_fields(current)}
            fields.update(source)
            model = self.__build_model(key, fields, fields["unique_code"])
            if model.unique_code != current.unique_code:
                self.__ensure_unreferenced(current)
            self.__validate_change(model, current)
            current.replace_state(model)
            return current

    """Удалить сущность, если на неё нет ссылок."""
    def delete(self, key: str, unique_code: str) -> None:
        with self.__lock:
            model = self.find(key, unique_code)
            self.__ensure_unreferenced(model)
            self.get(key).remove(model)

    """Собрать модель через общий десериализатор и разрешить ссылки по коду."""
    def __build_model(self, key: str, source: dict, code: str) -> abstract_model:
        model_type = self.__models[key].__name__
        if source.get("model_type", model_type) != model_type:
            raise argument_exception("model_type", "Тип модели не соответствует справочнику")
        fields = {name: list(value) if isinstance(value, tuple) else value
                  for name, value in source.items()}
        references = {model.unique_code: model for items in self.__data.values() for model in items}
        return deserializer().deserialize(
            {**fields, "model_type": model_type, "unique_code": code}, references
        )

    """Запретить удаление и смену кода используемой модели."""
    def __ensure_unreferenced(self, target: abstract_model) -> None:
        for items in self.__data.values():
            for model in items:
                if model is not target and any(item is target for item in self.__references(model)):
                    raise conflict_exception(f"Сущность используется: {target.unique_code}")

    """Вернуть ссылки сущности, включая ссылки из строк рецепта."""
    @staticmethod
    def __references(model: abstract_model):
        for reference in model.references():
            if isinstance(reference, receipt_item_model):
                yield from reference.references()
            else:
                yield reference

    """Проверить код, существование ссылок и отсутствие циклов."""
    def __validate_change(self, model: abstract_model, current: abstract_model = None) -> None:
        known = {item.unique_code: item for items in self.__data.values() for item in items}
        if model.unique_code in known and known[model.unique_code] is not current:
            raise conflict_exception(f"Код уже используется: {model.unique_code}")
        pending = list(self.__references(model))
        visited = set()
        while pending:
            reference = pending.pop()
            if reference is current or reference is model:
                raise conflict_exception("Циклическая ссылка")
            if known.get(reference.unique_code) is not reference:
                raise argument_exception("unique_code", f"Неизвестная ссылка: {reference.unique_code}")
            if reference.unique_code not in visited:
                visited.add(reference.unique_code)
                pending.extend(self.__references(reference))

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
