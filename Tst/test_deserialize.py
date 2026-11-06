import copy
import json
import pytest
from Src.Core.abstract_model_factory import abstract_model_factory
from Src.Core.validator import argument_exception, operation_exception
from Src.Logics.convert_factory import convert_factory
from Src.Logics.deserializer import deserializer
from Src.Logics.model_factory import model_factory
from Src.Logics.storage_manager import storage_manager
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.receipt_item_model import receipt_item_model
from Src.Models.receipt_model import receipt_model
from Src.Models.storage_model import storage_model


"""
Получить первичные данные в отдельном экземпляре хранилища,
не оставляя singleton для остальных тестов
"""
@pytest.fixture
def source_data(monkeypatch):
    monkeypatch.delattr(storage_manager, "instance", raising=False)
    try:
        yield storage_manager().data
    finally:
        del storage_manager.instance


"""
Сериализовать модель или хранилище существующей фабрикой конвертеров
"""
def serialize(source) -> dict:
    return convert_factory().create(source).convert(source)


"""
<summary>
Фабрика создает новую модель указанного типа и наследует абстрактную фабрику
</summary>
"""
@pytest.mark.parametrize("model_type, model_class", [
    ("group", group_model),
    ("range", range_model),
    ("nomenclature", nomenclature_model),
    ("storage", storage_model),
    ("receipt", receipt_model),
    ("receipt_item", receipt_item_model),
])
def test_equals_model_factory_create(model_type, model_class):
    # Подготовка
    factory = model_factory()

    # Действие
    model = factory.create(model_type)

    # Проверка
    assert isinstance(factory, abstract_model_factory)
    assert isinstance(model, model_class)
    assert factory.create(model_type) is not model


"""
<summary>
Неизвестный тип модели или неверный тип аргумента приводит к argument_exception
</summary>
"""
@pytest.mark.parametrize("model_type", ["unknown", "", None, 42])
def test_raise_model_factory_create_unknown_type(model_type):
    # Действие и проверка
    with pytest.raises(argument_exception):
        model_factory().create(model_type)


"""
<summary>
Каждый справочник восстанавливается из JSON в модели с исходными полями и кодами.
Загруженные объекты являются новыми экземплярами
</summary>
"""
@pytest.mark.parametrize("key, model_class", [
    ("group", group_model),
    ("range", range_model),
    ("nomenclature", nomenclature_model),
    ("storage", storage_model),
    ("receipt", receipt_model),
])
def test_equals_deserializer_deserialize_models(source_data, key, model_class):
    # Подготовка
    original = source_data[key][0]
    source = json.loads(json.dumps(serialize(original), ensure_ascii=False))

    # Действие
    loaded = deserializer().deserialize(source, key)

    # Проверка
    assert isinstance(loaded, model_class)
    assert loaded is not original
    assert loaded.unique_code == original.unique_code
    assert serialize(loaded) == serialize(original)


"""
<summary>
После сериализации и чтения JSON все справочники хранилища восстанавливаются
без потери записей, полей и кодов
</summary>
"""
def test_equals_deserializer_deserialize_storage(source_data):
    # Подготовка
    expected = serialize(source_data)
    source = json.loads(json.dumps(expected, ensure_ascii=False))

    # Действие
    loaded = deserializer().deserialize(source)

    # Проверка
    assert loaded.keys() == source_data.keys()
    assert serialize(loaded) == expected
    for key, originals in source_data.items():
        assert len(loaded[key]) == len(originals)
        for original, restored in zip(originals, loaded[key]):
            assert type(restored) is type(original)
            assert restored is not original
            assert restored.unique_code == original.unique_code


"""
<summary>
Повторяющиеся в JSON ссылки становятся общими объектами: номенклатура использует
группы и единицы из загруженных справочников, килограмм ссылается на тот же грамм
</summary>
"""
def test_equals_deserializer_deserialize_shared_references(source_data):
    # Подготовка
    source = serialize(source_data)

    # Действие
    loaded = deserializer().deserialize(source)
    ranges = {item.unique_code: item for item in loaded["range"]}
    groups = {item.unique_code: item for item in loaded["group"]}

    # Проверка
    assert loaded["range"][1].base is loaded["range"][0]
    for item in loaded["nomenclature"]:
        assert item.group is groups[item.group.unique_code]
        assert item.range is ranges[item.range.unique_code]


"""
<summary>
Рецепт восстанавливает полуфабрикат, упаковку, шаги и веса.
Его строки ссылаются на модели из загруженного хранилища
</summary>
"""
def test_equals_deserializer_deserialize_nested_receipt(source_data):
    # Подготовка
    source = serialize(source_data)

    # Действие
    loaded = deserializer().deserialize(source)
    dough, receipt = loaded["receipt"]
    nomenclatures = {item.unique_code: item for item in loaded["nomenclature"]}

    # Проверка
    assert receipt.items[0].receipt is dough
    assert receipt.items[0].nomenclature is None
    assert len(dough.items) == 4
    assert receipt.items[1].nomenclature is nomenclatures[receipt.items[1].nomenclature.unique_code]
    assert receipt.items[2].nomenclature.group.name == "Упаковка"
    assert receipt.steps == source_data["receipt"][1].steps
    assert receipt.brutto == 585
    assert receipt.netto == 579


"""
<summary>
Веса рецепта вычисляются по восстановленным строкам, значения brutto и netto
из JSON не присваиваются модели
</summary>
"""
def test_equals_deserializer_deserialize_calculated_weights(source_data):
    # Подготовка
    source = serialize(source_data["receipt"][1])
    source["brutto"] = -1
    source["netto"] = -1

    # Действие
    loaded = deserializer().deserialize(source, "receipt")

    # Проверка
    assert loaded.brutto == 585
    assert loaded.netto == 579


"""
<summary>
Три уровня вложенности сохраняются после чтения JSON. Изменение состава
загруженного полуфабриката пересчитывает вес блюда и не меняет исходную модель
</summary>
"""
def test_equals_deserializer_deserialize_three_levels():
    # Подготовка
    gram = range_model.create_gram()
    sugar = nomenclature_model.create("Сахар", group_model.create("Сырьё"), gram)
    filling = receipt_model.create("Начинка", 1, 5)
    filling.add_item(receipt_item_model.create(sugar, gram, 50, waste=10))
    preparation = receipt_model.create("Полуфабрикат", 1, 10)
    preparation.add_item(receipt_item_model.create_from_receipt(filling, 2))
    dish = receipt_model.create("Блюдо", 1, 20)
    dish.add_item(receipt_item_model.create_from_receipt(preparation))
    source = json.loads(json.dumps(serialize(dish)))

    # Действие
    loaded = deserializer().deserialize(source, "receipt")
    loaded_filling = loaded.items[0].receipt.items[0].receipt

    # Проверка
    assert loaded.brutto == 100
    assert loaded.netto == 90
    loaded_filling.remove_item(loaded_filling.items[0].nomenclature)
    assert loaded.brutto == 0
    assert loaded.netto == 0
    assert dish.brutto == 100


"""
<summary>
Общие ссылки восстанавливаются независимо от порядка справочников в JSON
</summary>
"""
def test_equals_deserializer_deserialize_catalog_order(source_data):
    # Подготовка
    source = dict(reversed(list(serialize(source_data).items())))

    # Действие
    loaded = deserializer().deserialize(source)
    dough = loaded["receipt"][0]
    cottage_cheese = loaded["nomenclature"][1]

    # Проверка
    assert dough.items[0].nomenclature is cottage_cheese
    assert loaded["range"][1].base is loaded["range"][0]


"""
<summary>
Каждый вызов десериализации создает независимый набор моделей
</summary>
"""
def test_not_same_deserializer_deserialize_repeated_call():
    # Подготовка
    source = serialize(group_model.create("Сырьё"))
    loader = deserializer()

    # Действие
    first = loader.deserialize(source, "group")
    second = loader.deserialize(source, "group")

    # Проверка
    assert first is not second
    assert first.unique_code == second.unique_code


"""
<summary>
Одинаковый код с разными данными или типами модели приводит к argument_exception
</summary>
"""
@pytest.mark.parametrize("conflict", ["name", "type"])
def test_raise_deserializer_deserialize_conflicting_code(source_data, conflict):
    # Подготовка
    source = copy.deepcopy(serialize(source_data))
    if conflict == "name":
        source["nomenclature"][0]["group"]["name"] = "Другая группа"
    else:
        source["group"][0]["unique_code"] = source["range"][0]["unique_code"]

    # Действие и проверка
    with pytest.raises(argument_exception):
        deserializer().deserialize(source)


"""
<summary>
Неизвестный справочник, неверная структура JSON, неизвестное поле или отсутствие
кода модели приводят к argument_exception
</summary>
"""
@pytest.mark.parametrize("source", [
    None,
    [],
    {"unknown": []},
    {"range": {}},
    {"group": [{"name": "Сырьё"}]},
    {"group": [{"unique_code": "group-1", "name": 42}]},
    {"group": [{"unique_code": "group-1", "name": "Сырьё", "unknown": 1}]},
])
def test_raise_deserializer_deserialize_invalid_source(source):
    # Действие и проверка
    with pytest.raises(argument_exception):
        deserializer().deserialize(source)


"""
<summary>
Циклическая ссылка по коду базовой единицы не приводит к бесконечной рекурсии,
а отклоняется с argument_exception
</summary>
"""
def test_raise_deserializer_deserialize_cycle():
    # Подготовка
    source = serialize(range_model.create_kilogram())
    source["base"]["unique_code"] = source["unique_code"]

    # Действие и проверка
    with pytest.raises(argument_exception):
        deserializer().deserialize(source, "range")


"""
<summary>
Некорректное количество ингредиента в JSON отклоняется с argument_exception
</summary>
"""
@pytest.mark.parametrize("quantity", [0, -1, True, "100", float("nan"), float("inf")])
def test_raise_deserializer_deserialize_invalid_quantity(source_data, quantity):
    # Подготовка
    source = serialize(source_data["receipt"][0].items[0])
    source["quantity"] = quantity

    # Действие и проверка
    with pytest.raises(argument_exception):
        deserializer().deserialize(source, "receipt_item")


"""
<summary>
Десериализатор читает JSON-файл, созданный существующей сериализацией хранилища
</summary>
"""
def test_equals_deserializer_load_json_file(source_data, tmp_path):
    # Подготовка
    source = serialize(source_data)
    file_name = tmp_path / "storage.json"
    file_name.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")

    # Действие
    loaded = deserializer().load(str(file_name))

    # Проверка
    assert serialize(loaded) == source


"""
<summary>
Отсутствующий файл или некорректный текст JSON приводят к operation_exception
</summary>
"""
@pytest.mark.parametrize("contents", [None, "не JSON"])
def test_raise_deserializer_load_invalid_file(tmp_path, contents):
    # Подготовка
    file_name = tmp_path / "storage.json"
    if contents is not None:
        file_name.write_text(contents, encoding="utf-8")

    # Действие и проверка
    with pytest.raises(operation_exception):
        deserializer().load(str(file_name))
