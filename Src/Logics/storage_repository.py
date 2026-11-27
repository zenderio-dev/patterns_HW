from copy import copy

from Src.Core.abstract_model import abstract_model
from Src.Core.validator import validator, conflict_exception, operation_exception


class storage_repository:
    """Хранит доменные объекты по коду и считает входящие ссылки."""

    def __init__(self):
        """Создать пустой репозиторий."""
        self.__roots = {}
        self.__data = {}
        self.__counts = {}

    def registry(self, source: abstract_model) -> None:
        """Зарегистрировать объект вместе с его связями."""
        self.registry_range([source])

    def registry_range(self, items: list) -> None:
        """Зарегистрировать коллекцию целиком после проверки кодов и связей."""
        validator.validate(items, list)
        roots = self.__roots.copy()
        for item in items:
            validator.validate(item, abstract_model)
            if item.unique_code in roots and roots[item.unique_code] is not item:
                raise conflict_exception(f"Код уже используется: {item.unique_code}")
            roots[item.unique_code] = item
        self.__rebuild(roots)

    def get(self, source: str) -> abstract_model:
        """Получить доменный объект по уникальному коду."""
        validator.validate(source, str)
        if source not in self.__data:
            raise operation_exception(f"Не найдена доменная сущность по коду: {source}")
        return self.__data[source]

    def can_delete(self, source: abstract_model) -> bool:
        """Проверить, что объект зарегистрирован и на него нет ссылок."""
        validator.validate(source, abstract_model)
        code = source.unique_code
        return self.__roots.get(code) is source and self.__counts[code] == 0

    def delete(self, source: abstract_model) -> None:
        """Удалить свободный объект и пересчитать ссылки."""
        if not self.can_delete(source):
            raise conflict_exception(f"Невозможно удалить запись: {source.unique_code}")
        roots = self.__roots.copy()
        del roots[source.unique_code]
        self.__rebuild(roots)

    def replace(self, source: abstract_model, replacement: abstract_model) -> None:
        """Обновить объект с сохранением его идентичности и пересчитать ссылки."""
        code = source.unique_code
        new_code = replacement.unique_code
        if self.__roots.get(code) is not source or (code != new_code and not self.can_delete(source)):
            raise conflict_exception(f"Невозможно изменить код записи: {code}")
        if code != new_code and new_code in self.__data:
            raise conflict_exception(f"Код уже используется: {new_code}")

        previous = copy(source)
        roots = self.__roots.copy()
        del roots[code]
        roots[new_code] = source
        source.replace_state(replacement)
        try:
            self.__rebuild(roots)
        except conflict_exception:
            source.replace_state(previous)
            raise

    def __rebuild(self, roots: dict) -> None:
        """Пересчитать индекс целиком, считая каждую связь один раз."""
        data = {}
        counts = {}
        active = set()
        for item in roots.values():
            self.__visit(item, data, counts, active)
        self.__roots, self.__data, self.__counts = roots, data, counts

    def __visit(self, item: abstract_model, data: dict, counts: dict, active: set) -> None:
        """Проверить объект и учесть его исходящие связи."""
        code = item.unique_code
        if code in active:
            raise conflict_exception(f"Циклическая ссылка: {code}")
        if code in data:
            if data[code] is not item:
                raise conflict_exception(f"Код уже используется: {code}")
            return

        data[code] = item
        counts[code] = 0
        active.add(code)
        for reference in item.references():
            self.__visit(reference, data, counts, active)
            counts[reference.unique_code] += 1
        active.remove(code)

    @property
    def data(self) -> dict:
        """Вернуть копию индекса объектов по коду."""
        return self.__data.copy()

    @property
    def counts(self) -> dict:
        """Вернуть копию счётчиков входящих ссылок."""
        return self.__counts.copy()
