from Src.Core.abstract_model import abstract_model
from Src.Core.event_publisher import events
from Src.Models.company_model import company_model
from Src.Core.validator import validator, argument_exception
from Src.Dtos.report_type_enum import report_type_enum

"""
Модель настроек приложения: организация и ответственные лица
"""
class settings_model(abstract_model):
    """Карточка организации"""
    _company:company_model = None
    """Наименование директора"""
    _boss_name:str = ""
    """Наименование главного бухгалтера"""
    _account_name:str = ""
    """Флаг. Первый старт - нужно сформировать первичные данные"""
    _first_start:bool = True
    """Формат ответа"""
    _response_format:report_type_enum = report_type_enum.TXT
    """Признак действующих настроек приложения."""
    __track_changes = False

    def track_changes(self, enabled: bool) -> None:
        """Включить публикацию изменений действующих настроек."""
        self.__track_changes = enabled
        if self._company is not None:
            self._company.track_changes(enabled)

    def __change(self, field: str, value) -> None:
        """Сохранить параметр и сообщить об изменении его значения."""
        attribute = f"_{field}"
        previous = getattr(self, attribute)
        setattr(self, attribute, value)
        if self.__track_changes and previous != value:
            events.publish("settings", "INFO", f"Изменён параметр: {field}")

    """Определить плоский формат файла настроек."""
    @classmethod
    def is_flat(cls, source: dict) -> bool:
        return not source or any(
            field.startswith("company_") or isinstance(getattr(cls, field, None), property)
            for field in source if isinstance(field, str)
        )

    """Подготовить поля модели и карточку организации из плоских настроек."""
    @classmethod
    def flat_fields(cls, source: dict) -> dict:
        prefix = "company_"
        company_fields = {field[len(prefix):]: value for field, value in source.items()
                          if isinstance(field, str) and field.startswith(prefix)
                          and field != "company_unique_code"}
        fields = {field: value for field, value in source.items()
                  if isinstance(field, str) and field not in ("company", "unique_code")
                  and isinstance(getattr(cls, field, None), property)}
        fields["company"] = company_model.from_dict(company_fields)
        return fields

    """Восстановить настройки и применить значения по умолчанию."""
    @classmethod
    def from_dict(cls, source: dict) -> 'settings_model':
        result = cls()
        for field, value in source.items():
            if not isinstance(getattr(cls, field, None), property):
                continue
            if field == "response_format":
                validator.validate(value, str)
                if value.upper() not in report_type_enum.__members__:
                    raise argument_exception("response_format", "Неизвестный формат отчёта")
                value = report_type_enum[value.upper()]
            setattr(result, field, value)
        return result


    """
    Наименование организации
    """
    @property
    def company(self) -> company_model:
        return self._company

    @company.setter
    def company(self, value: company_model) -> None:
        validator.validate(value, company_model)
        if not self.__track_changes:
            self._company = value
            return

        previous = self._company
        before = {}
        if previous is not None:
            before = previous.parameters()
            previous.track_changes(False)
        self._company = value
        value.track_changes(True)
        for field, current in value.parameters().items():
            if before.get(field) != current:
                events.publish("settings", "INFO", f"Изменён параметр: {field}")


    """
    Наименование директора
    """
    @property
    def boss_name(self) -> str:
        return self._boss_name

    @boss_name.setter
    def boss_name(self, value: str) -> None:
        validator.validate(value, str, 255)
        self.__change("boss_name", value.strip())

    """
    Наименование главного бухгалтера
    """
    @property
    def account_name(self) -> str:
        return self._account_name

    @account_name.setter
    def account_name(self, value: str) -> None:
        validator.validate(value, str, 255)
        self.__change("account_name", value.strip())

    """
    Флаг. Первый старт
    """
    @property
    def first_start(self) -> bool:
        return self._first_start

    @first_start.setter
    def first_start(self, value: bool) -> None:
        validator.validate(value, bool)
        self.__change("first_start", value)

    """
    Формат ответа
    """
    @property
    def response_format(self) -> report_type_enum:
        return self._response_format

    @response_format.setter
    def response_format(self, value: report_type_enum) -> None:
        validator.validate(value, report_type_enum)
        self.__change("response_format", value)
