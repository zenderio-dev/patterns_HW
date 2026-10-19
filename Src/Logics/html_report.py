import html
from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в формате HTML
"""
class html_report(abstract_report):

    """
    Сформировать отчет: HTML-таблица на каждый раздел
    """
    def build(self, source) -> report_result_dto:
        lines = []
        for _, header, rows in self._sections(source):
            lines += ["<table>", self.__row(header, "th")]
            lines += [self.__row(row, "td") for row in rows]
            lines.append("</table>")

        result = report_result_dto()
        result.text = "\n".join(lines)
        return result

    """
    Тип содержимого отчета
    """
    @property
    def content_type(self) -> str:
        return "text/html"

    """
    Расширение файла отчета
    """
    @property
    def file_extension(self) -> str:
        return "html"

    """
    Строка HTML-таблицы с ячейками tag
    """
    @staticmethod
    def __row(values: list, tag: str) -> str:
        cells = "".join(f"<{tag}>{html.escape(str(value))}</{tag}>" for value in values)
        return f"<tr>{cells}</tr>"
