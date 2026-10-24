from Src.Core.abstract_report_factory import abstract_report_factory
from Src.Core.abstract_report import abstract_report
from Src.Core.validator import validator, argument_exception
from Src.Dtos.report_type_enum import report_type_enum
from Src.Models.settings_model import settings_model
from Src.Logics.text_report import text_report
from Src.Logics.csv_report import csv_report
from Src.Logics.markdown_report import markdown_report
from Src.Logics.xml_report import xml_report
from Src.Logics.html_report import html_report

"""
Фабрика отчетов. Хранит настройки и создает отчет нужного формата
"""
class report_factory(abstract_report_factory):
    __settings: settings_model = None
    __mapping: dict = {
        report_type_enum.TXT: text_report,
        report_type_enum.CSV: csv_report,
        report_type_enum.MARKDOWN: markdown_report,
        report_type_enum.XML: xml_report,
        report_type_enum.HTML: html_report,
    }

    """
    Создать фабрику с настройками
    """
    def __init__(self, settings: settings_model):
        validator.validate(settings, settings_model)
        self.__settings = settings

    """
    Создать отчет указанного формата
    """
    def create(self, report_type: report_type_enum) -> abstract_report:
        validator.validate(report_type, report_type_enum)
        return self.__mapping[report_type]()

    """
    Создать отчет по названию формата (без учета регистра)
    """
    def create_by_name(self, name: str) -> abstract_report:
        validator.validate(name, str)
        if name.upper() not in report_type_enum.__members__:
            raise argument_exception("name", f"Неизвестный формат отчета: {name}")
        return self.create(report_type_enum[name.upper()])

    """
    Создать отчет в формате из настроек (response_format)
    """
    def create_default(self) -> abstract_report:
        return self.create(self.__settings.response_format)

    """
    Список названий реализованных форматов отчетов
    """
    def formats(self) -> list:
        return [report_type.name for report_type in self.__mapping]

    """
    Текущие настройки
    """
    @property
    def settings(self) -> settings_model:
        return self.__settings
