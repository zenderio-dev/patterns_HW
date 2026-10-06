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
группа «Сырьё», склад и номенклатура из ингредиентов рецепта Docs/Recipe.md
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
    assert groups == ["Сырьё"]
    assert nomenclatures == ["Пшеничная мука", "Сахар", "Сливочное масло", "Яйца", "Ванилин"]
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
    manager.load()

    # Проверка
    assert not manager.is_loaded
    for items in manager.data.values():
        assert len(items) == 0

    settings.first_start = True
    manager.load()
