from Src.Models.company_model import company_model
from Src.Models.storage_model import storage_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.group_model import group_model
import uuid
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
