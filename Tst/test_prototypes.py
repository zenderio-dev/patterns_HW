import pytest
from datetime import date
from decimal import Decimal

from Src.Core.validator import argument_exception
from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.filter_type_enum import filter_type_enum
from Src.Logics.filter_prototype import filter_prototype
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.receipt_model import receipt_model


@pytest.fixture
def models():
    """Создать связанные справочники для проверки общего прототипа."""
    group = group_model.create("Сырьё")
    gram = range_model.create_gram()
    kilogram = range_model.create_kilogram(gram)
    flour = nomenclature_model.create("Мука", group, kilogram)
    return group, gram, kilogram, flour


"""
<summary>
Один прототип отбирает все четыре типа моделей по имени и уникальному коду.
</summary>
"""
@pytest.mark.parametrize("kind", ["group", "range", "nomenclature", "receipt"])
@pytest.mark.parametrize("field", ["name", "unique_code"])
def test_equals_filter_prototype_clone_models(models, kind, field):
    group, gram, kilogram, flour = models
    model = {"group": group, "range": kilogram, "nomenclature": flour,
             "receipt": receipt_model.create("Сырники", 2, 10)}[kind]
    prototype = filter_prototype([model])
    condition = filter_dto(field, filter_type_enum.EQUALS, getattr(model, field))

    result = prototype.clone(condition)

    assert result is not prototype
    assert result.data == (model,)
    assert result.data[0] is model


"""
<summary>
LIKE находит подстроку без учёта регистра. Клонирование цепочкой сохраняет исходный набор.
</summary>
"""
def test_equals_filter_prototype_clone_chain():
    first = group_model.create("Молочные продукты")
    second = group_model.create("Молочное сырьё")
    items = [first, second]
    prototype = filter_prototype(items)
    items.clear()

    selected = prototype.clone(filter_dto("name", filter_type_enum.LIKE, "МОЛО"))
    result = selected.clone(filter_dto("unique_code", filter_type_enum.EQUALS, second.unique_code))

    assert prototype.data == (first, second)
    assert selected.data == (first, second)
    assert result.data == (second,)
    assert prototype.clone(filter_dto("name", filter_type_enum.EQUALS, "молочное сырьё")).data == ()
    assert prototype.clone(filter_dto("name", filter_type_enum.LIKE, "нет")).data == ()


"""
<summary>
Поиск проходит по базовой единице и связанным моделям, пропуская пустую ссылку.
</summary>
"""
def test_equals_filter_prototype_clone_nested(models):
    group, gram, kilogram, flour = models
    units = filter_prototype([gram, kilogram])
    assert units.clone(filter_dto("base.name", filter_type_enum.EQUALS, "грамм")).data == (kilogram,)
    result = filter_prototype([flour]).clone(
        filter_dto("range.base.unique_code", filter_type_enum.EQUALS, gram.unique_code)
    )
    assert result.data == (flour,)
    assert filter_prototype([]).clone(filter_dto()).data == ()


"""
<summary>
Некорректные поля и операции фильтра отклоняются внутренним исключением.
</summary>
"""
@pytest.mark.parametrize("source", [
    {"field": "value", "operation": "EQUALS", "value": "1"},
    {"field": "__dict__.name", "operation": "LIKE", "value": "x"},
    {"field": "name", "operation": "UNKNOWN", "value": "x"},
    {"field": "name", "value": 42},
    {"field": "name"},
    {"unknown": "x"},
])
def test_raise_filter_dto_from_dict_invalid(source):
    with pytest.raises(argument_exception):
        filter_dto.from_dict(source)


"""
<summary>
ОСВ учитывает движения до периода в начальном остатке, обе границы периода
и пересчёт единиц. Движение после периода не влияет на результат.
</summary>
"""
def test_equals_turnover_prototype_build_period(models):
    from Src.Logics.turnover_prototype import turnover_prototype
    from Src.Models.storage_model import storage_model
    from Src.Models.transaction_model import transaction_model

    group, gram, kilogram, flour = models
    warehouse = storage_model.create("Склад", "Иркутск")
    transactions = [
        transaction_model.create(flour, warehouse, kilogram, 1, date(2026, 1, 1)),
        transaction_model.create(flour, warehouse, kilogram, 2, date(2026, 1, 2)),
        transaction_model.create(flour, warehouse, gram, -500, date(2026, 1, 3)),
        transaction_model.create(flour, warehouse, kilogram, 9, date(2026, 1, 4)),
    ]
    original = turnover_prototype(transactions)
    selected = original.clone(filter_dto.from_dict({
        "field": "nomenclature.name", "operation": "EQUALS", "value": "Мука",
        "date_from": "2026-01-02", "date_to": "2026-01-03",
    }))
    rows = selected.build()

    assert isinstance(selected, turnover_prototype)
    assert len(original.data) == 4
    assert len(rows) == 1
    assert rows[0]["opening"] == 1000
    assert rows[0]["income"] == 2000
    assert rows[0]["expense"] == 500
    assert rows[0]["closing"] == 2500
    assert rows[0]["range_code"] == gram.unique_code
    assert selected.clone(filter_dto("storage.unique_code", filter_type_enum.EQUALS, "missing")).build() == []
    assert transactions[1].base_value() == Decimal("2000")


"""
<summary>
Некорректный период фильтра ОСВ отклоняется до формирования ведомости.
</summary>
"""
@pytest.mark.parametrize("source", [
    {"date_from": "wrong"},
    {"date_from": "2026-02-01", "date_to": "2026-01-01"},
    {"date_to": 2026},
])
def test_raise_filter_dto_from_dict_invalid_period(source):
    with pytest.raises(argument_exception):
        filter_dto.from_dict(source)


"""
<summary>
Движение отклоняет неконечное или нулевое количество и несовместимую единицу измерения.
</summary>
"""
@pytest.mark.parametrize("value", [True, 0, "1", float("nan"), float("inf")])
def test_raise_transaction_model_create_invalid_quantity(models, value):
    from Src.Models.storage_model import storage_model
    from Src.Models.transaction_model import transaction_model

    warehouse = storage_model.create("Склад", "Иркутск")
    with pytest.raises(argument_exception):
        transaction_model.create(models[3], warehouse, models[1], value, date(2026, 1, 1))


"""
<summary>
Один путь фильтра обходит строки рецепта и не теряет исходные объекты.
</summary>
"""
def test_equals_filter_prototype_clone_receipt_items(models):
    from Src.Models.receipt_item_model import receipt_item_model

    receipt = receipt_model.create("Тесто", 1, 10)
    receipt.add_item(receipt_item_model.create(models[3], models[1], 100))
    prototype = filter_prototype([receipt])
    selected = prototype.clone(filter_dto("items.nomenclature.group.name", filter_type_enum.EQUALS, "Сырьё"))
    assert selected.data == (receipt,)
    assert selected.data[0] is prototype.data[0]
    assert prototype.clone(filter_dto("items.nomenclature.name", filter_type_enum.LIKE, "нет")).data == ()


"""
<summary>
ОСВ разделяет склады, сохраняет отрицательный остаток и точно складывает дробные движения.
</summary>
"""
def test_equals_turnover_prototype_build_warehouses(models):
    from Src.Logics.turnover_prototype import turnover_prototype
    from Src.Models.storage_model import storage_model
    from Src.Models.transaction_model import transaction_model

    first = storage_model.create("Первый", "Иркутск")
    second = storage_model.create("Второй", "Иркутск")
    movements = [
        transaction_model.create(models[3], first, models[1], -50, date(2026, 1, 1)),
        transaction_model.create(models[3], second, models[1], 0.1, date(2026, 1, 2)),
        transaction_model.create(models[3], second, models[1], 0.2, date(2026, 1, 2)),
    ]
    prototype = turnover_prototype(movements).clone(filter_dto(date_from=date(2026, 1, 2)))
    rows = prototype.build()
    assert [row["storage_code"] for row in rows] == [first.unique_code, second.unique_code]
    assert rows[0]["opening"] == rows[0]["closing"] == -50
    assert rows[1]["income"] == rows[1]["closing"] == 0.3
    assert turnover_prototype([]).build() == []


"""
<summary>
Движение проходит сериализацию и десериализацию с датой и доменными ссылками.
</summary>
"""
def test_equals_transaction_model_serialization(models):
    from Src.Logics.convert_factory import convert_factory
    from Src.Logics.deserializer import deserializer
    from Src.Models.storage_model import storage_model
    from Src.Models.transaction_model import transaction_model

    warehouse = storage_model.create("Склад", "Иркутск")
    source = transaction_model.create(models[3], warehouse, models[2], 2, date(2026, 1, 2))
    data = convert_factory().create(source).convert(source)
    assert data["date"] == "2026-01-02"
    restored = deserializer().deserialize(data)
    assert restored.unique_code == source.unique_code
    assert restored.date == source.date
    assert restored.base_value() == source.base_value()
    assert restored.nomenclature.range is restored.range
    with pytest.raises(argument_exception):
        transaction_model.create(models[3], warehouse, range_model.create_piece(), 1, date(2026, 1, 2))
