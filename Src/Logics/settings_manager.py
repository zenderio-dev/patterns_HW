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

    """Singleton"""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(settings_manager, cls).__new__(cls)
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
            with open(inner_file_name, "r", encoding="utf-8") as file:
                self.__data = json.load(file)
                self.__is_loaded = self.convert()
                self._file_name = inner_file_name
        except Exception as ex:
            raise operation_exception(f"Ошибка при загрузке и обработки файла: {inner_file_name}. Детали:{ex}")

    """
    Преобразование загруженного JSON в модель настроек
    """
    def convert(self) -> bool:
        company_data = self.__data["company"]
        company = company_model()
        company.name = company_data["name"]
        company.inn = company_data["inn"]
        company.bic = company_data["bic"]
        company.corr_account = company_data["corr_account"]
        company.account = company_data["account"]
        company.ownership = company_data["ownership"]

        settings = settings_model()
        settings.company = company
        settings.boss_name = self.__data["boss_name"]
        settings.account_name = self.__data["account_name"]

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