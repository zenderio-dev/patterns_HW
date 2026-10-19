from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в текстовом формате
"""
class text_report(abstract_report):

    """
    Сформировать отчет: строки со значениями через " | ", разделы через пустую строку
    """
    def build(self, source) -> report_result_dto:
        blocks = []
        for _, header, rows in self._sections(source):
            blocks.append("\n".join(" | ".join(str(value) for value in row) for row in [header] + rows))

        result = report_result_dto()
        result.text = "\n\n".join(blocks)
        return result

    """
    Тип содержимого отчета
    """
    @property
    def content_type(self) -> str:
        return "text/plain"

    """
    Расширение файла отчета
    """
    @property
    def file_extension(self) -> str:
        return "txt"
