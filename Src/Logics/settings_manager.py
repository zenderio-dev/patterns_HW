from Src.Core.abstract_manager import abstract_manager
from Src.Core.validator import validator, operation_exception
import json
from Src.Models.settings_model import settings_model
from Src.Models.company_model import company_model

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
    Преобразование загруженного JSON в модель настроек.
    Ключи, которых нет в файле, пропускаются - остаются значения по умолчанию.
    Если данные некорректны - используются настройки по умолчанию
    """
    def convert(self) -> bool:
        settings = settings_model()
        try:
            company = company_model()
            company_data = self.__data.get("company", {})
            for field in ("name", "inn", "bic", "corr_account", "account", "ownership"):
                if field in company_data:
                    setattr(company, field, company_data[field])
            settings.company = company

            for field in ("boss_name", "account_name"):
                if field in self.__data:
                    setattr(settings, field, self.__data[field])
        except Exception:
            self.__settings = settings_model()
            return False

        self.__settings = settings
        return True

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