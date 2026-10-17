import html
from Src.Core.abstract_report import abstract_report
from Src.Dtos.report_result_dto import report_result_dto

"""
Отчет в формате HTML
"""
class html_report(abstract_report):

    """
    Сформировать отчет: HTML-таблица
    """
    def build(self, source) -> report_result_dto:
        header, rows = self._table(source)
        lines = ["<table>", self.__row(header, "th")]
        lines += [self.__row(row, "td") for row in rows]
        lines.append("</table>")

        result = report_result_dto()
        result.text = "\n".join(lines)
        return result

    """
    Строка HTML-таблицы с ячейками tag
    """
    @staticmethod
    def __row(values: list, tag: str) -> str:
        cells = "".join(f"<{tag}>{html.escape(str(value))}</{tag}>" for value in values)
        return f"<tr>{cells}</tr>"
