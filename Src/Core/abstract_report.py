from abc import ABC, abstractmethod
from Src.Core.validator import argument_exception
from Src.Dtos.report_result_dto import report_result_dto
from Src.Models.range_model import range_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.receipt_model import receipt_model

"""
Абстрактный класс для формирования отчета
"""
class abstract_report(ABC):

    """
    Сформировать отчет по модели
    """
    @abstractmethod
    def build(self, source) -> report_result_dto:
        pass

    """
    Представить модель в виде таблицы: заголовок и строки
    """
    def _table(self, source) -> tuple:
        if isinstance(source, receipt_model):
            header = ["Код", "Наименование", "Брутто", "Нетто"]
            rows = [[item.unique_code, item.component.name, item.brutto, item.netto] for item in source.items]
            return header, rows

        if isinstance(source, nomenclature_model):
            header = ["Код", "Наименование", "Группа", "Единица измерения"]
            return header, [[source.unique_code, source.name, source.group.name, source.range.name]]

        if isinstance(source, range_model):
            base = source.base.name if source.base is not None else ""
            header = ["Код", "Наименование", "Коэффициент", "Базовая единица"]
            return header, [[source.unique_code, source.name, source.value, base]]

        raise argument_exception("source", "Отчет для указанной модели не поддерживается")
