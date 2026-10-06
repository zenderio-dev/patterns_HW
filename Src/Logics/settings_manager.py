from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import validator, operation_exception
import json
from Src.Models.settings_model import settings_model

"""
Менеджер настроек (singleton). Загружает настройки приложения из JSON-файла
"""
class settings_manager(abstract_manager):
    __deffault_file_name: str = "settings.json"
    __settings: settings_model = None
    __data: dict = None
    __is_loaded: bool = False

    """Singleton"""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(settings_manager, cls).__new__(cls)
        return cls.instance

    """
    Загрузка данных
    """
    def load (self, file_name = ""):
        inner_file_name = file_name.strip() if file_name and file_name.strip() != "" else self.__deffault_file_name
        validator.validate(inner_file_name, str)

        try:
            with open(inner_file_name, "r", encoding="utf-8") as file:
                self.__data = json.load(file)
        except Exception as ex:
            raise operation_exception(f"Ошибка при загрузке файла: {inner_file_name}. Детали:{ex}")

        self.__is_loaded = self.convert()

    """
    Модель настроек
    """
    @property
    def settings(self) -> settings_model:
        return self.__settings
