import csv
import io
import xml.etree.ElementTree as ElementTree
import pytest
from Src.Dtos.report_type_enum import report_type_enum
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
Вспомогательная функция: номенклатура «Пшеничная мука» в группе «Сырьё», единица «кг»
</summary>
"""
def create_nomenclature() -> nomenclature_model:
    return nomenclature_model.create("Пшеничная мука", group_model.create("Сырьё"), range_model.create_kilogram())

"""
<summary>
Вспомогательная функция: рецепт «Сырники» - мука 60 г и яйцо 1 шт (50 г, отходы 12 %)
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
Отчёт по рецепту в любом формате содержит каждую строку рецепта с брутто и нетто
</summary>
"""
@pytest.mark.parametrize("report_type", list(report_type_enum))
def test_contains_report_build_receipt(report_type):
    # Подготовка
    report = report_factory(settings_model()).create(report_type)

    # Действие
    content = get_content(report.build(create_receipt()))

    # Проверка
    assert "Пшеничная мука" in content
    assert "Яйца" in content
    assert "50" in content
    assert "44" in content

"""
<summary>
CSV-отчёт по рецепту: заголовок и по одной строке на каждый ингредиент
с точными значениями брутто и нетто
</summary>
"""
def test_equals_csv_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    content = csv_report().build(receipt).binary.decode("utf-8")
    rows = list(csv.reader(io.StringIO(content), delimiter=";"))

    # Проверка
    assert rows[0] == ["Код", "Наименование", "Брутто", "Нетто"]
    assert len(rows) == 3
    assert rows[1][1:] == ["Пшеничная мука", "60", "60.0"]
    assert rows[2][1:] == ["Яйца", "50", "44.0"]

"""
<summary>
XML-отчёт по рецепту: корректный XML, по одному элементу row на каждый ингредиент
</summary>
"""
def test_equals_xml_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    root = ElementTree.fromstring(xml_report().build(receipt).text)
    rows = root.findall("row")

    # Проверка
    assert len(rows) == 2
    assert [field.text for field in rows[1]][1:] == ["Яйца", "50", "44.0"]

"""
<summary>
Markdown-отчёт по рецепту: таблица из заголовка, разделителя и строки на каждый ингредиент
</summary>
"""
def test_equals_markdown_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    lines = markdown_report().build(receipt).binary.decode("utf-8").splitlines()

    # Проверка
    assert len(lines) == 4
    assert lines[0] == "| Код | Наименование | Брутто | Нетто |"
    assert lines[1] == "| --- | --- | --- | --- |"
    assert lines[3].endswith("| Яйца | 50 | 44.0 |")

"""
<summary>
HTML-отчёт по рецепту: таблица из строки заголовка и строки на каждый ингредиент
</summary>
"""
def test_equals_html_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    content = html_report().build(receipt).text

    # Проверка
    assert content.startswith("<table>")
    assert content.count("<tr>") == 3
    assert content.count("<th>") == 4

"""
<summary>
Текстовый отчёт по рецепту: строка заголовка и строка на каждый ингредиент
</summary>
"""
def test_equals_text_report_build_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    lines = text_report().build(receipt).text.splitlines()

    # Проверка
    assert len(lines) == 3
    assert lines[0] == "Код | Наименование | Брутто | Нетто"
    assert lines[2].endswith("| Яйца | 50 | 44.0")
