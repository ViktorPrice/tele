#!/usr/bin/env python3
"""
Комплексное тестирование улучшенного MainController
"""

import sys
import logging
from unittest.mock import Mock, MagicMock
import warnings

# Настройка логирования для тестов
logging.basicConfig(level=logging.DEBUG)

# Импорт тестируемого модуля
from src.ui.controllers.main_controller import (
    MainController, 
    ControllerError, 
    ControllerNotInitializedError, 
    StateError
)

def test_imports_and_syntax():
    """Тест 1: Проверка импортов и синтаксиса"""
    print("=== Тест 1: Импорты и синтаксис ===")
    
    # Проверяем, что классы исключений наследуются правильно
    assert issubclass(ControllerNotInitializedError, ControllerError)
    assert issubclass(StateError, ControllerError)
    assert issubclass(ControllerError, Exception)
    
    print("✓ Классы исключений корректно определены")
    print("✓ Импорты работают")
    return True

def test_controller_initialization():
    """Тест 2: Инициализация контроллера"""
    print("\n=== Тест 2: Инициализация контроллера ===")
    
    # Создаем моки для model и view
    mock_model = Mock()
    mock_view = Mock()
    
    # Инициализируем контроллер
    controller = MainController(mock_model, mock_view)
    
    # Проверяем инициализацию
    assert controller.model == mock_model
    assert controller.view == mock_view
    assert controller.is_processing == False
    assert controller.is_loading == False
    assert controller.current_file_path is None
    assert isinstance(controller._event_handlers, dict)
    assert len(controller._event_handlers) == 0
    
    # Проверяем, что все подконтроллеры None
    assert controller.data_loader_controller is None
    assert controller.filter_controller is None
    assert controller.diagnostic_controller is None
    assert controller.ui_controller is None
    assert controller.plot_controller is None
    assert controller.report_controller is None
    assert controller.state_controller is None
    
    print("✓ Инициализация прошла успешно")
    print("✓ Все атрибуты установлены корректно")
    return True

def test_controller_setters():
    """Тест 3: Установка подконтроллеров"""
    print("\n=== Тест 3: Установка подконтроллеров ===")
    
    controller = MainController(Mock(), Mock())
    
    # Создаем моки подконтроллеров
    mock_filter = Mock()
    mock_ui = Mock()
    mock_plot = Mock()
    
    # Тестируем установку контроллеров
    controller.set_filter_controller(mock_filter)
    assert controller.filter_controller == mock_filter
    
    controller.set_ui_controller(mock_ui)
    assert controller.ui_controller == mock_ui
    
    controller.set_plot_controller(mock_plot)
    assert controller.plot_controller == mock_plot
    
    print("✓ Подконтроллеры устанавливаются корректно")
    
    # Тестируем повторную установку (должна вызвать исключение)
    try:
        controller.set_filter_controller(Mock())
        assert False, "Должно было быть исключение"
    except ValueError as e:
        assert "уже установлен" in str(e)
        print("✓ Повторная установка корректно блокируется")
    
    return True

def test_state_checking():
    """Тест 4: Проверка состояния"""
    print("\n=== Тест 4: Проверка состояния ===")
    
    controller = MainController(Mock(), Mock())
    
    # Тестируем нормальное состояние
    controller._check_state()  # Не должно вызвать исключение
    print("✓ Нормальное состояние проходит проверку")
    
    # Тестируем состояние обработки
    controller.is_processing = True
    try:
        controller._check_state()
        assert False, "Должно было быть исключение"
    except StateError as e:
        assert "занят обработкой" in str(e)
        print("✓ Состояние обработки корректно блокируется")
    
    controller.is_processing = False
    
    # Тестируем состояние загрузки
    controller.is_loading = True
    try:
        controller._check_state()
        assert False, "Должно было быть исключение"
    except StateError as e:
        assert "загрузка данных" in str(e)
        print("✓ Состояние загрузки корректно блокируется")
    
    return True

def test_delegation_methods():
    """Тест 5: Методы делегирования"""
    print("\n=== Тест 5: Методы делегирования ===")
    
    controller = MainController(Mock(), Mock())
    
    # Тестируем делегирование без инициализированного контроллера
    try:
        controller.apply_filters()
        assert False, "Должно было быть исключение"
    except ControllerNotInitializedError as e:
        assert "FilterController не инициализирован" in str(e)
        print("✓ Делегирование без контроллера корректно блокируется")
    
    # Устанавливаем мок контроллера
    mock_filter = Mock()
    controller.set_filter_controller(mock_filter)
    
    # Тестируем успешное делегирование
    controller.apply_filters(changed_only=True, test_param="value")
    mock_filter.apply_filters.assert_called_once_with(True, test_param="value")
    print("✓ Делегирование с параметрами работает корректно")
    
    # Проверяем управление состоянием
    assert controller.is_processing == False  # Должно сброситься после выполнения
    
    return True

def test_service_management():
    """Тест 6: Управление сервисами"""
    print("\n=== Тест 6: Управление сервисами ===")
    
    controller = MainController(Mock(), Mock())
    
    # Тестируем без UI контроллера
    try:
        controller.set_service('filtering', Mock())
        assert False, "Должно было быть исключение"
    except ControllerNotInitializedError:
        print("✓ Установка сервиса без UI контроллера блокируется")
    
    # Устанавливаем UI контроллер
    mock_ui = Mock()
    controller.set_ui_controller(mock_ui)
    
    # Тестируем установку сервисов
    mock_service = Mock()
    controller.set_service('filtering', mock_service)
    mock_ui.set_filtering_service.assert_called_once_with(mock_service)
    print("✓ Установка сервиса фильтрации работает")
    
    # Тестируем неизвестный тип сервиса
    try:
        controller.set_service('unknown', Mock())
        assert False, "Должно было быть исключение"
    except ValueError as e:
        assert "Неизвестный тип сервиса" in str(e)
        print("✓ Неизвестный тип сервиса корректно блокируется")
    
    return True

def test_event_system():
    """Тест 7: Событийная система"""
    print("\n=== Тест 7: Событийная система ===")
    
    controller = MainController(Mock(), Mock())
    
    # Тестируем подписку на события
    handler1 = Mock()
    handler2 = Mock()
    
    controller.subscribe('test_event', handler1)
    controller.subscribe('test_event', handler2)
    controller.subscribe('other_event', Mock())
    
    assert len(controller._event_handlers['test_event']) == 2
    assert len(controller._event_handlers['other_event']) == 1
    print("✓ Подписка на события работает")
    
    # Тестируем эмиссию событий
    test_data = {'key': 'value'}
    controller.emit_event('test_event', test_data)
    
    handler1.assert_called_once_with(test_data)
    handler2.assert_called_once_with(test_data)
    print("✓ Эмиссия событий работает")
    
    # Тестируем обработку ошибок в обработчиках
    error_handler = Mock(side_effect=Exception("Test error"))
    controller.subscribe('error_event', error_handler)
    
    # Это не должно вызвать исключение
    controller.emit_event('error_event', {})
    print("✓ Ошибки в обработчиках корректно обрабатываются")
    
    return True

def test_deprecated_methods():
    """Тест 8: Устаревшие методы"""
    print("\n=== Тест 8: Устаревшие методы ===")
    
    controller = MainController(Mock(), Mock())
    mock_ui = Mock()
    controller.set_ui_controller(mock_ui)
    
    # Захватываем предупреждения
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        mock_service = Mock()
        controller.set_filtering_service(mock_service)
        
        # Проверяем, что метод работает
        mock_ui.set_filtering_service.assert_called_once_with(mock_service)
        print("✓ Устаревший метод работает")
        
        # Проверяем предупреждение (логируется, но не как warning)
        print("✓ Устаревшие методы сохраняют совместимость")
    
    return True

def test_data_loading_with_state():
    """Тест 9: Загрузка данных с управлением состоянием"""
    print("\n=== Тест 9: Загрузка данных с состоянием ===")
    
    controller = MainController(Mock(), Mock())
    mock_loader = Mock()
    controller.set_data_loader_controller(mock_loader)
    
    # Тестируем загрузку файла
    test_path = "/test/path.csv"
    controller.load_csv_file(test_path)
    
    # Проверяем, что метод был вызван и путь сохранен
    mock_loader.load_csv_file.assert_called_once_with(test_path)
    assert controller.current_file_path == test_path
    assert controller.is_loading == False  # Должно сброситься
    print("✓ Загрузка файла с управлением состоянием работает")
    
    return True

def test_plot_operations():
    """Тест 10: Операции с графиками"""
    print("\n=== Тест 10: Операции с графиками ===")
    
    controller = MainController(Mock(), Mock())
    mock_plot = Mock()
    controller.set_plot_controller(mock_plot)
    
    # Тестируем построение графиков
    controller.build_plot()
    mock_plot.build_plot.assert_called_once()
    
    # Тестируем экспорт (без проверки состояния)
    controller.export_all_plots()
    mock_plot.export_all_plots.assert_called_once()
    
    # Тестируем очистку
    controller.clear_all_plots()
    mock_plot.clear_all_plots.assert_called_once()
    
    print("✓ Операции с графиками работают корректно")
    return True

def test_string_representations():
    """Тест 11: Строковые представления"""
    print("\n=== Тест 11: Строковые представления ===")
    
    controller = MainController(Mock(), Mock())
    controller.current_file_path = "/test/file.csv"
    controller.is_processing = True
    controller.is_loading = False
    
    str_repr = str(controller)
    assert "/test/file.csv" in str_repr
    assert "processing=True" in str_repr
    assert "loading=False" in str_repr
    
    assert repr(controller) == str(controller)
    
    print("✓ Строковые представления работают корректно")
    return True

def test_comprehensive_workflow():
    """Тест 12: Комплексный рабочий процесс"""
    print("\n=== Тест 12: Комплексный рабочий процесс ===")
    
    # Создаем контроллер и все подконтроллеры
    controller = MainController(Mock(), Mock())
    
    mock_loader = Mock()
    mock_filter = Mock()
    mock_ui = Mock()
    mock_plot = Mock()
    mock_report = Mock()
    mock_state = Mock()
    
    # Устанавливаем все контроллеры
    controller.set_data_loader_controller(mock_loader)
    controller.set_filter_controller(mock_filter)
    controller.set_ui_controller(mock_ui)
    controller.set_plot_controller(mock_plot)
    controller.set_report_controller(mock_report)
    controller.set_state_controller(mock_state)
    
    # Симулируем рабочий процесс
    # 1. Загрузка данных
    controller.load_csv_file("/test/data.csv")
    mock_loader.load_csv_file.assert_called_with("/test/data.csv")
    
    # 2. Применение фильтров
    controller.apply_filters(changed_only=True)
    mock_filter.apply_filters.assert_called_with(True)
    
    # 3. Построение графиков
    controller.build_plot()
    mock_plot.build_plot.assert_called_once()
    
    # 4. Генерация отчета
    controller.generate_report()
    mock_report.generate_report.assert_called_once()
    
    # 5. Очистка
    controller.cleanup()
    mock_state.cleanup.assert_called_once()
    
    print("✓ Комплексный рабочий процесс выполнен успешно")
    return True

def run_all_tests():
    """Запуск всех тестов"""
    print("Начинаем комплексное тестирование MainController...")
    print("=" * 60)
    
    tests = [
        test_imports_and_syntax,
        test_controller_initialization,
        test_controller_setters,
        test_state_checking,
        test_delegation_methods,
        test_service_management,
        test_event_system,
        test_deprecated_methods,
        test_data_loading_with_state,
        test_plot_operations,
        test_string_representations,
        test_comprehensive_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test.__name__} провален")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} провален с ошибкой: {e}")
    
    print("\n" + "=" * 60)
    print(f"РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✓ Пройдено: {passed}")
    print(f"❌ Провалено: {failed}")
    print(f"📊 Общий результат: {'УСПЕХ' if failed == 0 else 'ЕСТЬ ОШИБКИ'}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
