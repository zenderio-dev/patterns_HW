from abc import ABC, abstractmethod
from Src.Core.abstract_model import abstract_model
from Src.Core.entity_model import entity_model
from Src.Core.common import common
from Src.Core.validator import validator, argument_exception
from Src.Dtos.report_result_dto import report_result_dto
from Src.Dtos.report_section_dto import report_section_dto

"""
Абстрактный класс для формирования отчета
"""
class abstract_report(ABC):

    """
    Сформировать отчет по модели
    """
    @abstractmethod
    def build(self, source: abstract_model) -> report_result_dto:
        pass

    """
    Тип содержимого отчета
    """
    @property
    @abstractmethod
    def content_type(self) -> str:
        pass

    """
    Расширение файла отчета
    """
    @property
    @abstractmethod
    def file_extension(self) -> str:
        pass

    """
    Разделы отчета: свойства модели и списки вложенных моделей
    """
    def _sections(self, source: abstract_model) -> list:
        validator.validate(source, abstract_model)
        sections = [self.__section(type(source).__name__, [source])]
        for field in common.get_fields(source):
            value = getattr(source, field)
            if self.__is_models(value):
                sections.append(self.__section(field, value))
        return sections

    """
    Раздел отчета по непустому списку моделей
    """
    def __section(self, name: str, models) -> report_section_dto:
        if not self.__is_models(models):
            raise argument_exception("models", "Для раздела отчета нужен непустой список моделей")

        section = report_section_dto()
        section.name = name
        section.header = [field for field in common.get_fields(models[0])
                          if not isinstance(getattr(models[0], field), (list, tuple))]
        section.rows = [[self.__format(getattr(model, field)) for field in section.header] for model in models]
        return section

    """
    Признак непустого списка моделей
    """
    @staticmethod
    def __is_models(value) -> bool:
        return isinstance(value, (list, tuple)) and len(value) > 0 \
            and all(isinstance(item, abstract_model) for item in value)

    """
    Значение для отчета: сущность - наименование, модель - код, пустое значение - пустая строка
    """
    @staticmethod
    def __format(value):
        if value is None:
            return ""
        if isinstance(value, entity_model):
            return value.name
        if isinstance(value, abstract_model):
            return value.unique_code
        return value
