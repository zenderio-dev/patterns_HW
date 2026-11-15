from itertools import chain
from threading import RLock
from uuid import uuid4
from Src.Core.abstract_model import abstract_model
from Src.Core.common import common
from Src.Core.validator import validator, argument_exception, conflict_exception
from Src.Logics.deserializer import deserializer
from Src.Logics.storage_manager import storage_manager
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.receipt_item_model import receipt_item_model
from Src.Models.receipt_model import receipt_model
from Src.Models.storage_model import storage_model


class entity_service:
    """Операции изменения справочников и проверка связей между моделями."""

    __models = {
        storage_manager.range_key: range_model,
        storage_manager.group_key: group_model,
        storage_manager.nomenclature_key: nomenclature_model,
        storage_manager.storage_key: storage_model,
        storage_manager.receipt_key: receipt_model,
    }
    __lock = RLock()

    """Подключить хранилище справочников."""
    def __init__(self, storage: storage_manager):
        self.__storage = storage

    """Перебрать сущности всех справочников."""
    def __models_in_storage(self):
        return chain.from_iterable(self.__storage.data.values())

    """Собрать указатель на существующие модели по коду."""
    def __known_models(self) -> dict:
        return {model.unique_code: model for model in self.__models_in_storage()}

    """Добавить проверенную сущность в справочник."""
    def create(self, key: str, source: dict) -> abstract_model:
        with self.__lock:
            collection = self.__storage.get(key)
            validator.validate(source, dict)
            model = self.__build_model(key, source, source.get("unique_code", uuid4().hex))
            self.__validate_change(model)
            collection.append(model)
            return model

    """Обновить переданные поля, сохранив объект для существующих ссылок."""
    def update(self, key: str, unique_code: str, source: dict) -> abstract_model:
        with self.__lock:
            current = self.__storage.find(key, unique_code)
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
            model = self.__storage.find(key, unique_code)
            self.__ensure_unreferenced(model)
            self.__storage.get(key).remove(model)

    """Собрать модель через общий десериализатор и разрешить ссылки по коду."""
    def __build_model(self, key: str, source: dict, code: str) -> abstract_model:
        model_type = self.__models[key].__name__
        if source.get("model_type", model_type) != model_type:
            raise argument_exception("model_type", "Тип модели не соответствует справочнику")
        fields = {name: list(value) if isinstance(value, tuple) else value
                  for name, value in source.items()}
        references = self.__known_models()
        return deserializer().deserialize(
            {**fields, "model_type": model_type, "unique_code": code}, references
        )

    """Запретить удаление и смену кода используемой модели."""
    def __ensure_unreferenced(self, target: abstract_model) -> None:
        for model in self.__models_in_storage():
            if model is not target and any(reference is target for reference in self.__references(model)):
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
        known = self.__known_models()
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
