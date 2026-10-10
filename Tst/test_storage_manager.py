from Src.Logics.storage_manager import storage_manager
from Src.Logics.settings_manager import settings_manager

"""
<summary>
Первый старт: при первом создании менеджера первичные данные формируются
автоматически, без явного вызова load(). Тест должен идти первым в файле
</summary>
"""
def test_is_loaded_storage_manager_first_start():
    # Подготовка

    # Действие
    manager = storage_manager()

    # Проверка
    assert manager.is_loaded
    assert manager.data is not None


"""
<summary>
Первый старт: сформированы единицы измерения «грамм», «кг», «штука»,
группы «Сырьё» и «Упаковка», склад и номенклатура из ингредиентов рецепта Docs/Recipe.md
</summary>
"""
def test_equals_storage_manager_first_start_data():
    # Подготовка
    manager = storage_manager()

    # Действие
    ranges = [item.name for item in manager.data[storage_manager.range_key]]
    groups = [item.name for item in manager.data[storage_manager.group_key]]
    nomenclatures = [item.name for item in manager.data[storage_manager.nomenclature_key]]
    storages = manager.data[storage_manager.storage_key]

    # Проверка
    assert ranges == ["грамм", "кг", "штука"]
    assert groups == ["Сырьё", "Упаковка"]
    assert nomenclatures == ["Пшеничная мука", "Творог", "Сахар", "Яйца", "Растительное масло", "Контейнер для доставки"]
    assert len(storages) == 1


"""
<summary>
Каждый элемент хранилища уникален: уникальные коды всех моделей
во всех справочниках не повторяются
</summary>
"""
def test_unique_storage_manager_load_unique_codes():
    # Подготовка
    manager = storage_manager()

    # Действие
    codes = [item.unique_code for items in manager.data.values() for item in items]

    # Проверка
    assert len(codes) == len(set(codes))


"""
<summary>
Проверить, что storage_manager является синглтоном:
два вызова конструктора возвращают один и тот же объект
</summary>
"""
def test_equals_storage_manager_create():
    # Подготовка
    instance1 = storage_manager()
    instance2 = storage_manager()

    # Действие

    # Проверка
    assert instance1 is instance2


"""
<summary>
Проверить, что данные, сгенерированные через один экземпляр,
доступны через другой экземпляр
</summary>
"""
def test_is_loaded_storage_manager_load_other_instance():
    # Подготовка
    manager = storage_manager()

    # Действие
    manager.load()

    # Проверка
    assert storage_manager().is_loaded
    assert storage_manager().data is manager.data


"""
<summary>
Проверить, что после генерации все справочники заполнены
</summary>
"""
def test_not_empty_storage_manager_load_all_keys():
    # Подготовка
    manager = storage_manager()
    keys = (
        storage_manager.range_key,
        storage_manager.group_key,
        storage_manager.nomenclature_key,
        storage_manager.storage_key,
    )

    # Действие
    manager.load()

    # Проверка
    for key in keys:
        assert len(manager.data[key]) > 0


"""
<summary>
Проверить, что номенклатура ссылается на те же единицы измерения
и группы, что лежат в хранилище, а «кг» пересчитывается в граммы
</summary>
"""
def test_equals_storage_manager_load_nomenclature_links():
    # Подготовка
    manager = storage_manager()

    # Действие
    manager.load()
    ranges = manager.data[storage_manager.range_key]
    groups = manager.data[storage_manager.group_key]
    flour = manager.data[storage_manager.nomenclature_key][0]

    # Проверка
    assert flour.range in ranges
    assert flour.group in groups
    assert flour.range.name == "кг"
    assert flour.range.value == 1000
    assert flour.range.base.name == "грамм"
    assert flour.range.base is ranges[0]


"""
<summary>
Проверить, что модели хранилища хешируются: одна и та же модель,
добавленная в множество дважды, хранится в нём один раз
</summary>
"""
def test_equals_storage_manager_load_models_hashable():
    # Подготовка
    manager = storage_manager()

    # Действие
    manager.load()
    ranges = manager.data[storage_manager.range_key]
    unique_ranges = set(ranges + ranges)

    # Проверка
    assert len(unique_ranges) == len(ranges)


"""
<summary>
Кэширование: повторный вызов load() не пересоздаёт модели —
хранилище отдаёт те же объекты с теми же уникальными кодами
</summary>
"""
def test_equals_storage_manager_load_cached():
    # Подготовка
    manager = storage_manager()
    flour = manager.data[storage_manager.nomenclature_key][0]

    # Действие
    manager.load()

    # Проверка
    assert manager.data[storage_manager.nomenclature_key][0] is flour


"""
<summary>
Кэширование: load(force=True) формирует данные заново —
модели создаются повторно и получают новые уникальные коды
</summary>
"""
def test_not_equals_storage_manager_load_force():
    # Подготовка
    manager = storage_manager()
    flour = manager.data[storage_manager.nomenclature_key][0]

    # Действие
    manager.load(force=True)

    # Проверка
    new_flour = manager.data[storage_manager.nomenclature_key][0]
    assert new_flour is not flour
    assert new_flour.unique_code != flour.unique_code
    assert new_flour.name == flour.name


"""
<summary>
Не первый старт (settings.first_start = False): первичные данные не формируются,
справочники в хранилище пустые
</summary>
"""
def test_empty_storage_manager_load_not_first_start():
    # Подготовка
    settings = settings_manager().settings
    manager = storage_manager()
    settings.first_start = False

    # Действие
    manager.load(force=True)

    # Проверка
    assert not manager.is_loaded
    for items in manager.data.values():
        assert len(items) == 0

    settings.first_start = True
    manager.load(force=True)


"""
<summary>
Первый старт: сформирована технологическая карта «Сырники» с упаковкой для доставки -
4 порции, 30 минут, 6 строк (5 ингредиентов + контейнер), 6 шагов приготовления.
Брутто 585 г (400 + 50 + 60 + 40 + 20 + 15), нетто 579 г (яйцо: 50 г минус 12 % скорлупы = 44 г)
</summary>
"""
def test_equals_storage_manager_first_start_receipt():
    # Подготовка
    manager = storage_manager()

    # Действие
    receipt = manager.data[storage_manager.receipt_key][0]

    # Проверка
    assert receipt.name == "Сырники"
    assert receipt.portions == 4
    assert receipt.cooking_time == 30
    assert len(receipt.items) == 6
    assert len(receipt.steps) == 6
    assert receipt.brutto == 585
    assert receipt.netto == 579
    assert any(item.nomenclature.group.name == "Упаковка" for item in receipt.items)


"""
<summary>
Строки технологической карты ссылаются на те же объекты номенклатуры
и единиц измерения, что хранятся в справочниках хранилища
</summary>
"""
def test_equals_storage_manager_first_start_receipt_links():
    # Подготовка
    manager = storage_manager()
    nomenclatures = manager.data[storage_manager.nomenclature_key]
    ranges = manager.data[storage_manager.range_key]

    # Действие
    receipt = manager.data[storage_manager.receipt_key][0]

    # Проверка
    for item in receipt.items:
        assert any(item.nomenclature is nomenclature for nomenclature in nomenclatures)
        assert any(item.range is range for range in ranges)
