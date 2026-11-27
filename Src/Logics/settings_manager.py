from Src.Core.abstract_manager import abstract_manager
from Src.Core.common import common
from Src.Core.event_publisher import events
from Src.Core.validator import validator, argument_exception, operation_exception
from Src.Logics.deserializer import deserializer
from Src.Models.settings_model import settings_model

"""
Менеджер настроек (singleton). Загружает настройки приложения из JSON-файла
"""
class settings_manager(abstract_manager):
    __deffault_file_name: str = "settings.json"
    __settings: settings_model = None
    __data: dict = None
    __is_loaded: bool = False

    """Singleton. До загрузки файла доступны настройки по умолчанию"""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(settings_manager, cls).__new__(cls)
            cls.instance.__settings = settings_model()
            cls.instance.__settings.track_changes(True)
        return cls.instance

    """
    Загрузка данных. Уже загруженный файл берётся из кэша и повторно не читается.
    force = True - перечитать файл принудительно
    """
    def load (self, file_name = "", force: bool = False):
        inner_file_name = file_name.strip() if file_name and file_name.strip() != "" else self.__deffault_file_name
        validator.validate(inner_file_name, str)

        if self.__is_loaded and self._file_name == inner_file_name and not force:
            return

        try:
            self.__data = deserializer.read_json(inner_file_name)
        except operation_exception:
            events.publish("settings", "ERROR", "Не удалось прочитать файл настроек")
            raise

        self.__is_loaded = self.convert()
        self._file_name = inner_file_name

    """
    Преобразование загруженного JSON в модель настроек.
    JSON плоский: поля организации хранятся с префиксом company_ (company_inn и т.д.).
    Ключи, которых нет в файле, пропускаются - остаются значения по умолчанию.
    Если данные некорректны - используются настройки по умолчанию
    """
    def convert(self) -> bool:
        previous = self.__settings
        loaded = True
        try:
            current = deserializer().deserialize(self.__data)
            validator.validate(current, settings_model)
        except argument_exception:
            current = settings_model()
            loaded = False
            events.publish("settings", "ERROR", "Некорректные настройки")

        previous.track_changes(False)
        current.track_changes(True)
        self.__settings = current
        before = self.__parameters(previous)
        after = self.__parameters(current)
        for field in sorted(before.keys() | after.keys()):
            if before.get(field) != after.get(field):
                events.publish("settings", "INFO", f"Изменён параметр: {field}")
        return loaded

    @staticmethod
    def __parameters(settings: settings_model) -> dict:
        """Получить значения полей настроек и организации для сравнения."""
        result = {field: getattr(settings, field) for field in common.get_fields(settings)
                  if field not in ("unique_code", "company")}
        if settings.company is not None:
            result.update(settings.company.parameters())
        return result

    """
    Модель настроек
    """
    @property
    def settings(self) -> settings_model:
        return self.__settings

    """
    Признак успешной загрузки настроек
    """
    @property
    def is_loaded(self) -> bool:
        return self.__is_loaded
