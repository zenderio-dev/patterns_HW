from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в текстовом формате
"""
class text_report(abstract_report):

    """
    Сформировать отчет: строки со значениями через « | »
    """
    def build(self, source) -> report_result_dto:
        header, rows = self._table(source)
        lines = [" | ".join(str(value) for value in row) for row in [header] + rows]

        result = report_result_dto()
        result.text = "\n".join(lines)
        return result
