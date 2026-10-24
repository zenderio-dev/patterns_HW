import json
from datetime import datetime
import pytest
from Src.Core.entity_model import entity_model
from Src.Core.validator import argument_exception
from Src.Dtos.report_type_enum import report_type_enum
from Src.Logics.basic_convertor import basic_convertor
from Src.Logics.datetime_convertor import datetime_convertor
from Src.Logics.reference_convertor import reference_convertor
from Src.Logics.convert_factory import convert_factory
from Src.Models.range_model import range_model
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.receipt_model import receipt_model
from Src.Models.receipt_item_model import receipt_item_model

"""
<summary>
Тестовая модель с полями простых типов, даты, ссылки и списка
</summary>
"""
class sample_model(entity_model):
    __count: int = 5
    __price: float = 10.5
    __created: datetime = datetime(2026, 10, 24, 12, 0)
    __reference = None
    __items: tuple = ()

    """
    Количество
    """
    @property
    def count(self) -> int:
        return self.__count

    """
    Цена
    """
    @property
    def price(self) -> float:
        return self.__price

    """
    Дата создания
    """
    @property
    def created(self) -> datetime:
        return self.__created

    """
    Ссылка на другую модель
    """
    @property
    def reference(self):
        return self.__reference

    @reference.setter
    def reference(self, value):
        self.__reference = value

    """
    Список моделей
    """
    @property
    def items(self) -> tuple:
        return self.__items

    @items.setter
    def items(self, value: tuple):
        self.__items = value

"""
<summary>
Вспомогательная функция: тестовая модель «Образец» со ссылкой на группу и списком из единицы «грамм»
</summary>
"""
def create_sample() -> sample_model:
    sample = sample_model()
    sample.name = "Образец"
    sample.reference = group_model.create("Сырьё")
    sample.items = (range_model.create_gram(),)
    return sample

"""
<summary>
Вспомогательная функция: рецепт «Сырники» с полуфабрикатом «Тесто» (мука 400 г) и маслом 20 г
</summary>
"""
def create_receipt() -> receipt_model:
    gram = range_model.create_gram()
    raw = group_model.create("Сырьё")
    dough = receipt_model.create("Тесто", 4, 10)
    dough.add_item(receipt_item_model.create(nomenclature_model.create("Мука", raw, gram), gram, 400))
    receipt = receipt_model.create("Сырники", 4, 30)
    receipt.add_item(receipt_item_model.create_from_receipt(dough))
    receipt.add_item(receipt_item_model.create(nomenclature_model.create("Масло", raw, gram), gram, 20))
    receipt.add_step("Обжарьте сырники")
    return receipt

"""
<summary>
basic_convertor формирует словарь только по полям простых типов (числа, строки),
даты, ссылки и списки пропускает
</summary>
"""
def test_equals_basic_convertor_convert():
    # Подготовка
    sample = create_sample()

    # Действие
    result = basic_convertor().convert(sample)

    # Проверка
    assert result == {"count": 5, "name": "Образец", "price": 10.5, "unique_code": sample.unique_code}

"""
<summary>
basic_convertor сохраняет пустое значение поля как None
</summary>
"""
def test_equals_basic_convertor_convert_none():
    # Подготовка
    gram = range_model.create_gram()

    # Действие
    result = basic_convertor().convert(gram)

    # Проверка
    assert result["base"] is None

"""
<summary>
datetime_convertor формирует словарь только по полям-датам, дата - строка в формате ISO
</summary>
"""
def test_equals_datetime_convertor_convert():
    # Подготовка
    sample = create_sample()

    # Действие
    result = datetime_convertor().convert(sample)

    # Проверка
    assert result == {"created": "2026-10-24T12:00:00"}

"""
<summary>
reference_convertor формирует словарь по ссылкам и спискам: вложенные модели -
вложенные словари, список моделей - список словарей
</summary>
"""
def test_equals_reference_convertor_convert():
    # Подготовка
    sample = create_sample()

    # Действие
    result = reference_convertor(convert_factory()).convert(sample)

    # Проверка
    assert sorted(result.keys()) == ["items", "reference"]
    assert result["reference"] == {"name": "Сырьё", "unique_code": sample.reference.unique_code}
    assert result["items"][0]["name"] == "грамм"

"""
<summary>
reference_convertor без фабрики для вложенных объектов создать нельзя
</summary>
"""
def test_raise_reference_convertor_without_factory():
    # Действие и проверка
    with pytest.raises(argument_exception):
        reference_convertor(None)

"""
<summary>
Фабрика выбирает конвертер по типу значения: простые типы - basic, дата - datetime,
модель или список - reference, неподдерживаемый тип - None
</summary>
"""
@pytest.mark.parametrize("value, convertor_class", [
    (5, basic_convertor),
    (10.5, basic_convertor),
    ("строка", basic_convertor),
    (None, basic_convertor),
    (datetime(2026, 10, 24), datetime_convertor),
    (group_model.create("Сырьё"), reference_convertor),
    ([1, 2], reference_convertor),
])
def test_equals_convert_factory_create(value, convertor_class):
    # Подготовка
    factory = convert_factory()

    # Действие
    convertor = factory.create(value)

    # Проверка
    assert isinstance(convertor, convertor_class)

"""
<summary>
Для неподдерживаемого типа значения (Enum) фабрика конвертер не выбирает
</summary>
"""
def test_none_convert_factory_create_unsupported():
    # Действие
    convertor = convert_factory().create(report_type_enum.TXT)

    # Проверка
    assert convertor is None

"""
<summary>
Фабрика конвертирует простые значения как есть, дату - в строку ISO, список - в список
</summary>
"""
@pytest.mark.parametrize("value, expected", [
    (5, 5),
    ("строка", "строка"),
    (None, None),
    (datetime(2026, 10, 24, 12, 0), "2026-10-24T12:00:00"),
    ([1, "a"], [1, "a"]),
])
def test_equals_convert_factory_convert_simple(value, expected):
    # Действие
    result = convert_factory().convert(value)

    # Проверка
    assert result == expected

"""
<summary>
Фабрика конвертирует составной объект в словарь по всем полям:
простые типы, дату, ссылку и список с сохранением структуры
</summary>
"""
def test_equals_convert_factory_convert_object():
    # Подготовка
    sample = create_sample()

    # Действие
    result = convert_factory().convert(sample)

    # Проверка
    assert list(result.keys()) == ["count", "created", "items", "name", "price", "reference", "unique_code"]
    assert result["created"] == "2026-10-24T12:00:00"
    assert result["reference"]["name"] == "Сырьё"
    assert result["items"][0]["name"] == "грамм"

"""
<summary>
Номенклатура конвертируется с вложенными группой и единицей измерения,
а единица - со своей базовой единицей (кг -> грамм)
</summary>
"""
def test_equals_convert_factory_convert_nomenclature():
    # Подготовка
    nomenclature = nomenclature_model.create("Мука", group_model.create("Сырьё"), range_model.create_kilogram())

    # Действие
    result = convert_factory().convert(nomenclature)

    # Проверка
    assert result["name"] == "Мука"
    assert result["group"]["name"] == "Сырьё"
    assert result["range"]["name"] == "кг"
    assert result["range"]["value"] == 1000
    assert result["range"]["base"]["name"] == "грамм"
    assert result["range"]["base"]["base"] is None

"""
<summary>
Рецепт с полуфабрикатом конвертируется рекурсивно: строки рецепта - список словарей,
полуфабрикат - вложенный рецепт со своими строками, шаги - список строк
</summary>
"""
def test_equals_convert_factory_convert_receipt():
    # Подготовка
    receipt = create_receipt()

    # Действие
    result = convert_factory().convert(receipt)

    # Проверка
    assert result["name"] == "Сырники"
    assert result["brutto"] == 420
    assert result["steps"] == ["Обжарьте сырники"]
    assert len(result["items"]) == 2
    assert result["items"][0]["receipt"]["name"] == "Тесто"
    assert result["items"][0]["receipt"]["items"][0]["nomenclature"]["name"] == "Мука"
    assert result["items"][1]["nomenclature"]["name"] == "Масло"

"""
<summary>
Результат фабрики сериализуется в JSON и восстанавливается без потерь
</summary>
"""
def test_equals_convert_factory_convert_json():
    # Подготовка
    result = convert_factory().convert(create_receipt())

    # Действие
    text = json.dumps(result, ensure_ascii=False)

    # Проверка
    assert json.loads(text) == result
