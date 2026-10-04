# UML-диаграммы менеджеров

Оба менеджера — singleton: сколько раз ни вызывай конструктор, объект будет один.
И оба кэшируют данные: загрузили один раз — дальше отдают из памяти, пока не попросят `load(force=True)`.
На диаграммах показано только то, чем менеджеры пользуются снаружи — без приватных полей.

## settings_manager

Читает `settings.json` и собирает из него настройки с организацией внутри.

```mermaid
classDiagram
    direction LR

    class abstract_manager {
        <<abstract>>
        +load(file_name, force)
        +convert()
    }

    class settings_manager {
        <<singleton>>
        +load(file_name, force)
        +convert()
        +settings
        +is_loaded
    }

    class settings_model {
        +company
        +boss_name
        +account_name
    }

    class company_model {
        +name
        +inn
        +bic
        +corr_account
        +account
        +ownership
    }

    abstract_manager <|-- settings_manager : наследует
    settings_manager --> settings_model : хранит настройки
    settings_model --> company_model : организация

    note for settings_manager "load() читает settings.json один раз и кэширует,<br>повторно — только с force=True.<br>convert() собирает из файла модели"
```

## storage_manager

Хранит справочники. При первом обращении сам заполняется ингредиентами из [рецепта](Recipe.md).

```mermaid
classDiagram
    direction LR

    class abstract_manager {
        <<abstract>>
        +load(file_name, force)
        +convert()
    }

    class storage_manager {
        <<singleton>>
        +load(force)
        +convert()
        +data
        +is_loaded
    }

    class range_model {
        +name
        +value
        +base
    }

    class group_model {
        +name
    }

    class nomenclature_model {
        +name
        +group
        +range
    }

    class storage_model {
        +name
        +address
    }

    abstract_manager <|-- storage_manager : наследует
    storage_manager o-- range_model : единицы измерения
    storage_manager o-- group_model : группы
    storage_manager o-- nomenclature_model : номенклатура
    storage_manager o-- storage_model : склады
    nomenclature_model --> group_model : входит в группу
    nomenclature_model --> range_model : измеряется в
    range_model --> range_model : базовая единица

    note for storage_manager "При первом старте сам вызывает load():<br>создаёт грамм, кг, штуку, группу «Сырьё»,<br>склад и 5 ингредиентов вафель.<br>Дальше данные берутся из кэша"
    note for range_model "кг: value = 1000, base = грамм<br>грамм: value = 1, base нет"
```
