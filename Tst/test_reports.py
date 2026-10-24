import csv
import io
import xml.etree.ElementTree as ElementTree
import pytest
from Src.Core.validator import argument_exception
from Src.Dtos.report_type_enum import report_type_enum
from Src.Dtos.report_section_dto import report_section_dto
from Src.Logics.report_factory import report_factory
from Src.Logics.text_report import text_report
from Src.Logics.csv_report import csv_report
from Src.Logics.markdown_report import markdown_report
from Src.Logics.xml_report import xml_report
from Src.Logics.html_report import html_report
from Src.Models.settings_model import settings_model
from Src.Models.range_model import range_model
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.receipt_model import receipt_model
from Src.Models.receipt_item_model import receipt_item_model

"""
<summary>
Вспомогательная функция: номенклатура "Пшеничная мука" в группе "Сырьё", единица "кг"
</summary>
"""
def create_nomenclature() -> nomenclature_model:
    return nomenclature_model.create("Пшеничная мука", group_model.create("Сырьё"), range_model.create_kilogram())

"""
<summary>
Вспомогательная функция: рецепт "Сырники" - мука 60 г и яйцо 1 шт (50 г, отходы 12 %)
</summary>
"""
def create_receipt() -> receipt_model:
    gram = range_model.create_gram()
    piece = range_model.create_piece()
    egg = nomenclature_model.create("Яйца", group_model.create("Сырьё"), piece)
    receipt = receipt_model.create("Сырники", 4, 30)
    receipt.add_item(receipt_item_model.create(create_nomenclature(), gram, 60))
    receipt.add_item(receipt_item_model.create(egg, piece, 1, unit_weight=50, waste=12))
    return receipt

"""
<summary>
Вспомогательная функция: содержимое отчёта текстом (бинарные данные декодируются из UTF-8)
</summary>
"""
def get_content(result) -> str:
    return result.binary.decode("utf-8") if len(result.binary) > 0 else result.text

"""
<summary>
Фабрика отчётов создаёт отчёт нужного класса для каждого формата
</summary>
"""
@pytest.mark.parametrize("report_type, report_class", [
    (report_type_enum.TXT, text_report),
    (report_type_enum.CSV, csv_report),
    (report_type_enum.MARKDOWN, markdown_report),
    (report_type_enum.XML, xml_report),
    (report_type_enum.HTML, html_report),
])
def test_equals_report_factory_create(report_type, report_class):
    # Подготовка
    factory = report_factory(settings_model())

    # Действие
    report = factory.create(report_type)

    # Проверка
    assert isinstance(report, report_class)

"""
<summary>
create_default создаёт отчёт в формате, указанном в настройках фабрики (response_format)
</summary>
"""
def test_equals_report_factory_create_default():
    # Подготовка
    settings = settings_model()
    settings.response_format = report_type_enum.XML
    factory = report_factory(settings)

    # Действие
    report = factory.create_default()

    # Проверка
    assert isinstance(report, xml_report)

"""
<summary>
CSV и Markdown формируются как бинарные данные, остальные форматы - как текст
</summary>
"""
@pytest.mark.parametrize("report_type, is_binary", [
    (report_type_enum.TXT, False),
    (report_type_enum.CSV, True),
    (report_type_enum.MARKDOWN, True),
    (report_type_enum.XML, False),
    (report_type_enum.HTML, False),
])
def test_equals_report_build_binary_or_text(report_type, is_binary):
    # Подготовка
    report = report_factory(settings_model()).create(report_type)

    # Действие
    result = report.build(create_nomenclature())

    # Проверка
    assert (len(result.binary) > 0) == is_binary
    assert (result.text != "") != is_binary

"""
<summary>
Отчёт по номенклатуре в любом формате содержит код, наименование, группу и единицу измерения
</summary>
"""
@pytest.mark.parametrize("report_type", list(report_type_enum))
def test_contains_report_build_nomenclature(report_type):
    # Подготовка
    nomenclature = create_nomenclature()
    report = report_factory(settings_model()).create(report_type)

    # Действие
    content = get_content(report.build(nomenclature))

    # Проверка
    assert nomenclature.unique_code in content
    assert "Пшеничная мука" in content
    assert "Сырьё" in content
    assert "кг" in content

"""
<summary>
Отчёт по единице измерения в любом формате содержит наименование, коэффициент и базовую единицу
</summary>
"""
@pytest.mark.parametrize("report_type", list(report_type_enum))
def test_contains_report_build_range(report_type):
    # Подготовка
    report = report_factory(settings_model()).create(report_type)

    # Действие
    content = get_content(report.build(range_model.create_kilogram()))

    # Проверка
    assert "кг" in content
    assert "1000" in content
    assert "грамм" in content

"""
<summary>
Отчёт по рецепту в любом формате содержит сам рецепт (брутто 110, нетто 104)
и каждую его строку с брутто и нетто
</summary>
"""
@pytest.mark.parametrize("report_type", list(report_type_enum))
def test_contains_report_build_receipt(report_type):
    # Подготовка
    report = report_factory(settings_model()).create(report_type)

    # Действие
    content = get_content(report.build(create_receipt()))

    # Проверка
    assert "Сырники" in content
    assert "110" in content
    assert "104.0" in content
    assert "Пшеничная мука" in content
    assert "Яйца" in content
    assert "50" in content
    assert "44" in content

"""
<summary>
Фабрика создаёт отчёт по названию формата без учёта регистра
</summary>
"""
def test_equals_report_factory_create_by_name():
    # Подготовка
    factory = report_factory(settings_model())

    # Действие
    report = factory.create_by_name("markdown")

    # Проверка
    assert isinstance(report, markdown_report)

"""
<summary>
Неизвестное название формата приводит к исключению argument_exception
</summary>
"""
def test_raise_report_factory_create_by_name_unknown():
    # Подготовка
    factory = report_factory(settings_model())

    # Действие и проверка
    with pytest.raises(argument_exception):
        factory.create_by_name("pdf")

"""
<summary>
Каждый отчёт знает свой тип содержимого и расширение файла
</summary>
"""
@pytest.mark.parametrize("report_type, content_type, file_extension", [
    (report_type_enum.TXT, "text/plain", "txt"),
    (report_type_enum.CSV, "text/csv", "csv"),
    (report_type_enum.MARKDOWN, "text/markdown", "md"),
    (report_type_enum.XML, "application/xml", "xml"),
    (report_type_enum.HTML, "text/html", "html"),
])
def test_equals_report_content_type_file_extension(report_type, content_type, file_extension):
    # Подготовка
    report = report_factory(settings_model()).create(report_type)

    # Действие

    # Проверка
    assert report.content_type == content_type
    assert report.file_extension == file_extension

"""
<summary>
CSV-отчёт по рецепту: раздел рецепта (заголовок и строка), пустая строка,
раздел строк рецепта (заголовок и по строке на ингредиент)
</summary>
"""
def test_equals_csv_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    content = csv_report().build(receipt).binary.decode("utf-8")
    rows = list(csv.reader(io.StringIO(content), delimiter=";"))

    # Проверка
    assert len(rows) == 6
    assert rows[0] == ["brutto", "cooking_time", "name", "netto", "portions", "unique_code"]
    assert rows[1] == ["110", "30", "Сырники", "104.0", "4", receipt.unique_code]
    assert rows[2] == []
    assert rows[3][:4] == ["brutto", "component", "netto", "nomenclature"]
    assert rows[5][:4] == ["50", "Яйца", "44.0", "Яйца"]

"""
<summary>
XML-отчёт по рецепту: корректный XML из двух разделов - сам рецепт
и его строки (items), по элементу row на каждый ингредиент
</summary>
"""
def test_equals_xml_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    root = ElementTree.fromstring(xml_report().build(receipt).text)
    sections = root.findall("section")

    # Проверка
    assert len(sections) == 2
    assert len(sections[0].findall("row")) == 1
    assert sections[1].get("name") == "items"
    assert len(sections[1].findall("row")) == 2

"""
<summary>
Markdown-отчёт по рецепту: две таблицы - рецепт и строки рецепта
</summary>
"""
def test_equals_markdown_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    tables = markdown_report().build(receipt).binary.decode("utf-8").split("\n\n")

    # Проверка
    assert len(tables) == 2
    assert tables[0].splitlines()[0] == "| brutto | cooking_time | name | netto | portions | unique_code |"
    assert tables[0].splitlines()[1] == "| --- | --- | --- | --- | --- | --- |"
    assert len(tables[1].splitlines()) == 4

"""
<summary>
HTML-отчёт по рецепту: две таблицы - рецепт (заголовок и строка)
и строки рецепта (заголовок и две строки)
</summary>
"""
def test_equals_html_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    content = html_report().build(receipt).text

    # Проверка
    assert content.count("<table>") == 2
    assert content.count("<tr>") == 5

"""
<summary>
Текстовый отчёт по рецепту: два блока через пустую строку - рецепт и строки рецепта
</summary>
"""
def test_equals_text_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    blocks = text_report().build(receipt).text.split("\n\n")

    # Проверка
    assert len(blocks) == 2
    assert blocks[0].splitlines()[0] == "brutto | cooking_time | name | netto | portions | unique_code"
    assert len(blocks[1].splitlines()) == 3

"""
<summary>
Фабрика хранит переданные ей настройки
</summary>
"""
def test_equals_report_factory_settings():
    # Подготовка
    settings = settings_model()

    # Действие
    factory = report_factory(settings)

    # Проверка
    assert factory.settings is settings

"""
<summary>
Фабрика возвращает список названий всех реализованных форматов отчетов
</summary>
"""
def test_equals_report_factory_formats():
    # Подготовка
    factory = report_factory(settings_model())

    # Действие
    formats = factory.formats()

    # Проверка
    assert formats == ["TXT", "CSV", "MARKDOWN", "XML", "HTML"]

"""
<summary>
DTO раздела отчета хранит наименование, заголовок и строки
</summary>
"""
def test_equals_report_section_dto_values():
    # Подготовка
    section = report_section_dto()

    # Действие
    section.name = "items"
    section.header = ["brutto", "netto"]
    section.rows = [[50, 44.0]]

    # Проверка
    assert section.name == "items"
    assert section.header == ["brutto", "netto"]
    assert section.rows == [[50, 44.0]]

"""
<summary>
Значения неверного типа в DTO раздела отчета приводят к исключению argument_exception
</summary>
"""
@pytest.mark.parametrize("field, value", [
    ("name", 1),
    ("header", "brutto"),
    ("rows", "50"),
])
def test_raise_report_section_dto_invalid_value(field, value):
    # Подготовка
    section = report_section_dto()

    # Действие и проверка
    with pytest.raises(argument_exception):
        setattr(section, field, value)

"""
<summary>
Разделы отчета по рецепту - DTO report_section_dto: сам рецепт и его строки (items)
</summary>
"""
def test_equals_abstract_report_sections_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    sections = text_report()._sections(receipt)

    # Проверка
    assert all(isinstance(section, report_section_dto) for section in sections)
    assert [section.name for section in sections] == ["receipt_model", "items"]
    assert len(sections[1].rows) == 2

