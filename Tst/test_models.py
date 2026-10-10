from Src.Models.company_model import company_model
from Src.Models.storage_model import storage_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.group_model import group_model
import uuid
import pytest
from Src.Models.receipt_model import receipt_model
from Src.Models.receipt_item_model import receipt_item_model
from Src.Core.validator import argument_exception

"""
<summary>
Созданная модель организации имеет пустое наименование
</summary>
"""
def test_empty_company_model_createmodel():
    # Подготовка
    model = company_model()

    # Действие

    # Проверки
    assert model.name == ""

"""
<summary>
После присвоения наименования модель организации хранит непустое наименование
</summary>
"""
def test_not_empty_company_model_createmodel():
    # Подготовка
    model = company_model()
        
    # Действие
    model.name = "test"
        
    # Проверки
    assert model.name != ""

"""
<summary>
Две модели склада с одинаковым уникальным кодом равны
</summary>
"""
def test_equals_storage_model_create():
    # Подготовка
    id = uuid.uuid4().hex
    storage1 = storage_model()
    storage1.unique_code = id
    storage2 = storage_model()   
    storage2.unique_code = id

    # Действие 

    # Проверки
    assert storage1 == storage2

"""
<summary>
Две модели номенклатуры с одинаковым уникальным кодом равны
</summary>
"""
def test_equals_nomenclature_model_create():
    # Подготовка
    id = uuid.uuid4().hex
    item1 = nomenclature_model()
    item1.unique_code = id
    item2 = nomenclature_model()
    item2.unique_code = id

    # Действие

    # Проверки
    assert item1 == item2

"""
<summary>
Присвоение некорректного БИК (слишком длинное число) приводит к исключению argument_exception
</summary>
"""
def test_raise_company_model_fail_bik():
    # Подготовка
    company = company_model()

    # Действие и проверка
    try:
        company.bic = -99999999999
        assert False
    except argument_exception :
        assert True
    except:
        assert False

"""
<summary>
Фабричный метод create_kilogram без аргументов создаёт «кг» с коэффициентом 1000
и новой базовой единицей «грамм»
</summary>
"""
def test_equals_range_model_create_kilogram():
    # Подготовка

    # Действие
    kilogram = range_model.create_kilogram()

    # Проверки
    assert kilogram.name == "кг"
    assert kilogram.value == 1000
    assert kilogram.base.name == "грамм"
    assert kilogram.base.value == 1

"""
<summary>
Фабричный метод create_kilogram с переданным граммом использует именно его
в качестве базовой единицы, а не создаёт новый
</summary>
"""
def test_equals_range_model_create_kilogram_with_base():
    # Подготовка
    gram = range_model.create_gram()

    # Действие
    kilogram = range_model.create_kilogram(gram)

    # Проверки
    assert kilogram.base is gram

"""
<summary>
Вспомогательная функция: строка технологической карты с номенклатурой name
</summary>
"""
def create_receipt_item(name: str, quantity, range: range_model) -> receipt_item_model:
    nomenclature = nomenclature_model()
    nomenclature.name = name
    item = receipt_item_model()
    item.nomenclature = nomenclature
    item.range = range
    item.quantity = quantity
    return item

"""
<summary>
Строка в граммах без отходов: брутто = нетто = количество граммов
</summary>
"""
def test_equals_receipt_item_model_brutto_netto_gram():
    # Подготовка
    item = create_receipt_item("Сахар", 80, range_model.create_gram())

    # Действие

    # Проверки
    assert item.brutto == 80
    assert item.netto == 80

"""
<summary>
Строка в килограммах: масса единицы берётся из коэффициента «кг» (1000 г),
2 кг = 2000 г брутто
</summary>
"""
def test_equals_receipt_item_model_brutto_kilogram():
    # Подготовка
    item = create_receipt_item("Мука", 2, range_model.create_kilogram())

    # Действие

    # Проверки
    assert item.unit_weight == 1000
    assert item.brutto == 2000

"""
<summary>
Строка в штуках с массой единицы и отходами: 1 яйцо по 50 г, скорлупа 12 % -
брутто 50 г, нетто 44 г
</summary>
"""
def test_equals_receipt_item_model_netto_with_waste():
    # Подготовка
    piece = range_model()
    piece.name = "штука"
    item = create_receipt_item("Яйца", 1, piece)

    # Действие
    item.unit_weight = 50
    item.waste = 12

    # Проверки
    assert item.brutto == 50
    assert item.netto == 44

"""
<summary>
Некорректные количество, масса единицы или процент отходов
приводят к исключению argument_exception
</summary>
"""
@pytest.mark.parametrize("field, value", [
    ("quantity", 0), ("quantity", -1), ("quantity", "100"),
    ("unit_weight", 0), ("waste", -1), ("waste", 100), ("waste", True),
])
def test_raise_receipt_item_model_invalid_value(field, value):
    # Подготовка
    item = receipt_item_model()

    # Действие и проверка
    with pytest.raises(argument_exception):
        setattr(item, field, value)

"""
<summary>
Брутто и нетто технологической карты - суммы по строкам
</summary>
"""
def test_equals_receipt_model_brutto_netto_sum():
    # Подготовка
    gram = range_model.create_gram()
    receipt = receipt_model()
    egg = create_receipt_item("Яйца", 2, gram)
    egg.waste = 10

    # Действие
    receipt.add_item(create_receipt_item("Сахар", 80, gram))
    receipt.add_item(egg)

    # Проверки
    assert receipt.brutto == 82
    assert receipt.netto == 81.8

"""
<summary>
Один и тот же ингредиент нельзя добавить в технологическую карту дважды
</summary>
"""
def test_raise_receipt_model_add_item_duplicate():
    # Подготовка
    receipt = receipt_model()
    item = create_receipt_item("Сахар", 80, range_model.create_gram())
    receipt.add_item(item)
    duplicate = receipt_item_model()
    duplicate.nomenclature = item.nomenclature

    # Действие и проверка
    with pytest.raises(argument_exception):
        receipt.add_item(duplicate)

"""
<summary>
Фабричный метод range_model.create_piece создаёт единицу «штука» с коэффициентом 1
</summary>
"""
def test_equals_range_model_create_piece():
    # Действие
    piece = range_model.create_piece()

    # Проверки
    assert piece.name == "штука"
    assert piece.value == 1

"""
<summary>
Фабричный метод group_model.create создаёт группу с переданным наименованием
</summary>
"""
def test_equals_group_model_create_factory():
    # Действие
    group = group_model.create("Сырьё")

    # Проверки
    assert group.name == "Сырьё"

"""
<summary>
Фабричный метод storage_model.create создаёт склад с наименованием и адресом
</summary>
"""
def test_equals_storage_model_create_factory():
    # Действие
    storage = storage_model.create("Основной склад", "г. Иркутск")

    # Проверки
    assert storage.name == "Основной склад"
    assert storage.address == "г. Иркутск"

"""
<summary>
Фабричный метод nomenclature_model.create создаёт номенклатуру
с переданными группой и единицей измерения
</summary>
"""
def test_equals_nomenclature_model_create_factory():
    # Подготовка
    group = group_model.create("Сырьё")
    kilogram = range_model.create_kilogram()

    # Действие
    nomenclature = nomenclature_model.create("Творог", group, kilogram)

    # Проверки
    assert nomenclature.name == "Творог"
    assert nomenclature.group is group
    assert nomenclature.range is kilogram

"""
<summary>
Фабричный метод receipt_item_model.create создаёт строку технологической карты
с массой единицы и отходами: 1 яйцо по 50 г, 12 % - брутто 50 г, нетто 44 г
</summary>
"""
def test_equals_receipt_item_model_create_factory():
    # Подготовка
    piece = range_model.create_piece()
    egg = nomenclature_model.create("Яйца", group_model.create("Сырьё"), piece)

    # Действие
    item = receipt_item_model.create(egg, piece, 1, unit_weight=50, waste=12)

    # Проверки
    assert item.nomenclature is egg
    assert item.brutto == 50
    assert item.netto == 44

"""
<summary>
Фабричный метод receipt_model.create создаёт пустую технологическую карту
с наименованием, порциями и временем приготовления
</summary>
"""
def test_equals_receipt_model_create_factory():
    # Действие
    receipt = receipt_model.create("Сырники", 4, 30)

    # Проверки
    assert receipt.name == "Сырники"
    assert receipt.portions == 4
    assert receipt.cooking_time == 30
    assert len(receipt.items) == 0
    assert receipt.brutto == 0

"""
<summary>
Добавление ингредиента в технологическую карту увеличивает брутто и нетто
на массу этого ингредиента
</summary>
"""
def test_increase_receipt_model_add_item():
    # Подготовка
    gram = range_model.create_gram()
    receipt = receipt_model.create("Сырники", 4, 30)
    receipt.add_item(create_receipt_item("Творог", 400, gram))
    sugar = create_receipt_item("Сахар", 40, gram)

    # Действие
    receipt.add_item(sugar)

    # Проверки
    assert receipt.brutto == 440
    assert receipt.netto == 440

"""
<summary>
Исключение ингредиента из технологической карты уменьшает брутто и нетто
на массу этого ингредиента (с учётом отходов для нетто)
</summary>
"""
def test_decrease_receipt_model_remove_item():
    # Подготовка
    gram = range_model.create_gram()
    piece = range_model.create_piece()
    receipt = receipt_model.create("Сырники", 4, 30)
    receipt.add_item(create_receipt_item("Творог", 400, gram))
    egg = create_receipt_item("Яйца", 1, piece)
    egg.unit_weight = 50
    egg.waste = 12
    receipt.add_item(egg)

    # Действие
    receipt.remove_item(egg.nomenclature)

    # Проверки
    assert len(receipt.items) == 1
    assert receipt.brutto == 400
    assert receipt.netto == 400

"""
<summary>
Исключение ингредиента, которого нет в технологической карте,
приводит к исключению argument_exception
</summary>
"""
def test_raise_receipt_model_remove_item_missing():
    # Подготовка
    receipt = receipt_model.create("Сырники", 4, 30)
    missing = nomenclature_model.create("Соль", group_model.create("Сырьё"), range_model.create_gram())

    # Действие и проверка
    with pytest.raises(argument_exception):
        receipt.remove_item(missing)

