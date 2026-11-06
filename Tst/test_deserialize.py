import pytest
from Src.Core.abstract_model_factory import abstract_model_factory
from Src.Core.validator import argument_exception, operation_exception
from Src.Logics.model_factory import model_factory
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.receipt_item_model import receipt_item_model
from Src.Models.receipt_model import receipt_model
from Src.Models.storage_model import storage_model


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
