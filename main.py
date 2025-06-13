# main.py - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Точка входа приложения с полной интеграцией приоритетной логики изменяемых параметров
"""
import sys
import logging
import locale
import tkinter as tk
from pathlib import Path
import os
from datetime import datetime

def setup_encoding():
    """Настройка кодировки для Windows"""
    if sys.platform == 'win32':
        try:
            try:
                locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, 'ru_RU.cp1251')
                except locale.Error:
                    locale.setlocale(locale.LC_ALL, '')
        except:
            pass

def setup_safe_logging():
    """Безопасная настройка логирования с поддержкой русского языка"""

    class SafeWindowsFormatter(logging.Formatter):
        """Форматтер с безопасной обработкой для Windows"""

        def format(self, record):
            try:
                msg = super().format(record)

                # Заменяем проблемные Unicode символы на ASCII
                replacements = {
                    '✓': 'OK', '✅': 'OK', '❌': 'ERROR', '⚠️': 'WARNING',
                    '🔥': '[PRIORITY]', '→': '->', '←': '<-',
                    '—': '-', '…': '...'
                }

                for old, new in replacements.items():
                    msg = msg.replace(old, new)

                # Для Windows - принудительно кодируем в cp1251
                if sys.platform == 'win32':
                    try:
                        encoded = msg.encode('cp1251', errors='replace')
                        return encoded.decode('cp1251')
                    except:
                        return msg.encode('ascii', errors='replace').decode('ascii')

                return msg

            except Exception:
                return f"[ENCODING ERROR] {record.levelname}: {record.name}"

    # Создаем форматтер
    formatter = SafeWindowsFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Файловый обработчик БЕЗ UTF-8
    try:
        file_handler = logging.FileHandler(
            'telemetry_analyzer.log',
            encoding='cp1251',
            mode='w'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        print(f"Файл логов будет создан с cp1251 кодировкой: telemetry_analyzer.log")

    except Exception as e:
        print(f"Ошибка создания файлового логгера: {e}")
        file_handler = None

    # Консольный обработчик
    try:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
    except Exception as e:
        print(f"Ошибка создания консольного логгера: {e}")
        console_handler = logging.StreamHandler()

    # Настройка корневого логгера
    handlers = [h for h in [file_handler, console_handler] if h is not None]

    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
        force=True
    )

    # Тестируем логирование
    logger = logging.getLogger('EncodingTest')
    logger.info("Тест кодировки: русские символы OK")
    logger.info("Encoding test: English symbols OK")

def main():
    """Главная функция с полной интеграцией приоритетной логики"""
    setup_encoding()
    setup_safe_logging()

    logger = logging.getLogger(__name__)
    logger.info("=== ЗАПУСК ПРИЛОЖЕНИЯ С ПРИОРИТЕТНОЙ ЛОГИКОЙ ИЗМЕНЯЕМЫХ ПАРАМЕТРОВ ===")

    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src'))

        # Импорты с обработкой ошибок
        components = _import_components(logger)
        if not components:
            return

        # Создание приложения с приоритетной логикой
        app_context = _create_application_context_priority(components, logger)
        if not app_context:
            return

        # Запуск приложения
        _run_application(app_context, logger)

    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

def _import_components(logger):
    """Безопасный импорт компонентов с проверкой приоритетной логики"""
    try:
        logger.info("Импорт компонентов с приоритетной логикой...")
        
        from src.ui.views.main_window import MainWindow
        from src.ui.controllers.main_controller import MainController
        from src.core.domain.services.filtering_service import ParameterFilteringService
        from src.infrastructure.data.csv_loader import CSVDataLoader
        from src.infrastructure.plotting.core.plot_manager import PlotManager
        from src.infrastructure.reporting.core.report_manager import ReportManager
        from src.infrastructure.sop.core.sop_manager import SOPManager
        from src.core.models.data_model import DataModel

        # НОВОЕ: Импорт конфигурации UI
        try:
            from src.config.ui_config import (
                validate_ui_config, create_application_context_config,
                get_main_py_integration_instructions
            )
            ui_config_available = True
            logger.info("[PRIORITY] UI конфигурация доступна")
        except ImportError:
            ui_config_available = False
            logger.warning("UI конфигурация недоступна, используется fallback")

        # НОВОЕ: Импорт Use Cases для приоритетной логики
        try:
            from src.core.application.use_cases.find_changed_parameters_use_case import (
                FindChangedParametersUseCase, create_find_changed_parameters_use_case
            )
            use_cases_available = True
            logger.info("[PRIORITY] Use Cases для изменяемых параметров доступны")
        except ImportError:
            use_cases_available = False
            logger.warning("Use Cases недоступны, используется fallback")

        return {
            'MainWindow': MainWindow,
            'MainController': MainController,
            'ParameterFilteringService': ParameterFilteringService,
            'CSVDataLoader': CSVDataLoader,
            'PlotManager': PlotManager,
            'ReportManager': ReportManager,
            'SOPManager': SOPManager,
            'DataModel': DataModel,
            'ui_config_available': ui_config_available,
            'use_cases_available': use_cases_available
        }

    except ImportError as e:
        logger.error(f"Ошибка импорта компонентов: {e}")
        return None

def _create_application_context_priority(components, logger):
    """ИСПРАВЛЕННОЕ создание контекста приложения с приоритетной логикой"""
    try:
        logger.info("[PRIORITY] Создание контекста приложения с приоритетной логикой...")

        # Валидация UI конфигурации
        if components.get('ui_config_available'):
            from src.config.ui_config import validate_ui_config
            validation_result = validate_ui_config()
            if not validation_result['is_valid']:
                logger.warning(f"Проблемы с UI конфигурацией: {validation_result['errors']}")

        # Создание главного окна
        root = tk.Tk()
        root.title("Анализатор телеметрии - ПРИОРИТЕТНАЯ ЛОГИКА")
        root.geometry("1400x900")  # Увеличенное окно для лучшего UX

        # Создание модели данных с приоритетной поддержкой
        model = components['DataModel']()
        logger.info("[PRIORITY] DataModel создана с поддержкой изменяемых параметров")

        # ИСПРАВЛЯЕМ: Создание сервисов с правильными зависимостями
        services = _create_services_priority(components, model, logger)

        # Создание UI с приоритетной логикой
        main_window = components['MainWindow'](root)
        main_window.setup()
        logger.info("[PRIORITY] MainWindow создано")

        # Создание контроллера с приоритетной логикой
        main_controller = components['MainController'](model, main_window)
        logger.info("[PRIORITY] MainController создан")

        # КРИТИЧНО: Внедрение зависимостей с приоритетной логикой
        _inject_dependencies_priority(main_controller, services, logger)

        # НОВОЕ: Настройка приоритетной логики изменяемых параметров
        _setup_priority_logic(main_controller, main_window, components, logger)

        # Установка контроллера в UI
        main_window.set_controller(main_controller)

        # КРИТИЧНО: Установка контроллера в ui_components с приоритетной логикой
        if hasattr(main_window, 'ui_components'):
            main_window.ui_components.set_controller(main_controller)
            main_controller.set_ui_components(main_window.ui_components)

            # ИСПРАВЛЕНО: Установка панелей в контроллер с приоритетной логикой
            _setup_ui_panels_priority(main_controller, main_window.ui_components, logger)

        # НОВОЕ: Отладочная информация о приоритетной логике
        _debug_priority_setup(main_controller, main_window, logger)

        # Добавление обработчика закрытия окна
        def on_closing():
            try:
                logger.info("Закрытие приложения с приоритетной логикой")
                if hasattr(main_controller, 'save_filters'):
                    main_controller.save_filters()
                if hasattr(main_controller, 'cleanup'):
                    main_controller.cleanup()
                if hasattr(main_window, 'cleanup'):
                    main_window.cleanup()
            except Exception as e:
                logger.error(f"Ошибка при закрытии: {e}")
            finally:
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        logger.info("[PRIORITY] Контекст приложения создан с приоритетной логикой")

        return {
            'root': root,
            'model': model,
            'main_window': main_window,
            'main_controller': main_controller,
            'services': services
        }

    except Exception as e:
        logger.error(f"Ошибка создания контекста приложения: {e}")
        import traceback
        traceback.print_exc()
        return None

def _create_services_priority(components, model, logger):
    """НОВАЯ функция создания сервисов с приоритетной поддержкой"""
    try:
        logger.info("[PRIORITY] Создание сервисов с поддержкой изменяемых параметров...")

        # Получаем data_loader из модели
        data_loader = model.data_loader

        # Создание сервисов
        filtering_service = components['ParameterFilteringService'](data_loader)
        plot_manager = components['PlotManager'](data_loader)
        
        # ИСПРАВЛЕНО: Создание ReportManager с правильными параметрами
        try:
            # Пробуем создать с data_loader и plot_service
            report_manager = components['ReportManager'](
                data_loader=data_loader,
                plot_service=plot_manager
            )
            logger.info("[PRIORITY] ReportManager создан с data_loader и plot_service")
        except TypeError:
            try:
                # Пробуем создать только с data_loader
                report_manager = components['ReportManager'](data_loader)
                logger.info("[PRIORITY] ReportManager создан с data_loader")
            except TypeError:
                try:
                    # Пробуем создать без параметров
                    report_manager = components['ReportManager']()
                    logger.info("[PRIORITY] ReportManager создан без параметров")
                except Exception as e:
                    logger.error(f"Не удалось создать ReportManager: {e}")
                    report_manager = None
        
        sop_manager = components['SOPManager'](data_loader)

        # НОВОЕ: Создание Use Case для изменяемых параметров
        changed_params_use_case = None
        if components.get('use_cases_available'):
            try:
                from src.core.application.use_cases.find_changed_parameters_use_case import (
                    create_find_changed_parameters_use_case
                )
                changed_params_use_case = create_find_changed_parameters_use_case(model)
                logger.info("[PRIORITY] Use Case для изменяемых параметров создан")
            except Exception as e:
                logger.warning(f"Не удалось создать Use Case: {e}")

        services = {
            'filtering_service': filtering_service,
            'plot_manager': plot_manager,
            'report_manager': report_manager,
            'sop_manager': sop_manager,
            'changed_params_use_case': changed_params_use_case
        }

        logger.info("[PRIORITY] Все сервисы созданы с приоритетной поддержкой")
        return services

    except Exception as e:
        logger.error(f"Ошибка создания сервисов: {e}")
        return {}

def _inject_dependencies_priority(controller, services, logger):
    """ИСПРАВЛЕННОЕ внедрение зависимостей с приоритетной логикой"""
    try:
        logger.info("[PRIORITY] Внедрение зависимостей с приоритетной логикой...")

        # Устанавливаем фильтрационный сервис
        if 'filtering_service' in services:
            controller.set_filtering_service(services['filtering_service'])
            logger.info("[PRIORITY] ParameterFilteringService установлен")

        # Устанавливаем PlotManager
        if 'plot_manager' in services:
            controller.set_plot_manager(services['plot_manager'])
            logger.info("[PRIORITY] PlotManager установлен")

        # ИСПРАВЛЯЕМ: Устанавливаем ReportManager с множественными попытками
        if 'report_manager' in services and services['report_manager']:
            report_manager = services['report_manager']
            
            # Проверяем доступные методы установки
            if hasattr(controller, 'set_report_manager'):
                controller.set_report_manager(report_manager)
                logger.info("[PRIORITY] ReportManager установлен через set_report_manager")
            elif hasattr(controller, 'set_report_generator'):
                controller.set_report_generator(report_manager)
                logger.info("[PRIORITY] ReportManager установлен через set_report_generator")
            else:
                # Устанавливаем напрямую как атрибут
                controller.report_generator = report_manager
                logger.info("[PRIORITY] ReportManager установлен как атрибут report_generator")

        # Устанавливаем SOPManager
        if 'sop_manager' in services:
            controller.set_sop_manager(services['sop_manager'])
            logger.info("[PRIORITY] SOPManager установлен")

        # НОВОЕ: Устанавливаем Use Case для изменяемых параметров
        if 'changed_params_use_case' in services and services['changed_params_use_case']:
            if hasattr(controller, 'set_changed_params_use_case'):
                controller.set_changed_params_use_case(services['changed_params_use_case'])
                logger.info("[PRIORITY] Use Case для изменяемых параметров установлен")
            else:
                # Устанавливаем как атрибут
                controller.find_changed_params_use_case = services['changed_params_use_case']
                logger.info("[PRIORITY] Use Case установлен как атрибут")

        logger.info("[PRIORITY] Все зависимости внедрены с приоритетной логикой")

    except Exception as e:
        logger.error(f"Ошибка внедрения зависимостей: {e}")

def _setup_priority_logic(main_controller, main_window, components, logger):
    """НОВАЯ функция настройки приоритетной логики изменяемых параметров"""
    try:
        logger.info("[PRIORITY] Настройка приоритетной логики изменяемых параметров...")

        # Настройка приоритета в модели
        if hasattr(main_controller.model, 'set_priority_mode'):
            main_controller.model.set_priority_mode(True)
            logger.info("[PRIORITY] Приоритетный режим активирован в DataModel")

        # Настройка приоритета в UI компонентах
        if hasattr(main_window, 'ui_components') and main_window.ui_components:
            ui_components = main_window.ui_components

            # КРИТИЧНО: Настройка приоритета в TimePanel
            if hasattr(ui_components, 'time_panel') and ui_components.time_panel:
                time_panel = ui_components.time_panel
                
                if hasattr(time_panel, 'set_changed_params_priority'):
                    time_panel.set_changed_params_priority(True)
                    logger.info("[PRIORITY] TimePanel получил приоритет для изменяемых параметров")
                else:
                    logger.warning("[PRIORITY] TimePanel не имеет метода set_changed_params_priority")

            # КРИТИЧНО: Отключение дублированного чекбокса в FilterPanel
            if hasattr(ui_components, 'filter_panel') and ui_components.filter_panel:
                filter_panel = ui_components.filter_panel
                
                if hasattr(filter_panel, 'disable_changed_only_checkbox'):
                    filter_panel.disable_changed_only_checkbox()
                    logger.info("[PRIORITY] Дублированный чекбокс в FilterPanel отключен")

                # Настройка синхронизации с TimePanel
                if hasattr(filter_panel, '_sync_with_time_panel'):
                    filter_panel._sync_with_time_panel()
                    logger.info("[PRIORITY] FilterPanel синхронизирован с TimePanel")

            # НОВОЕ: Настройка диагностической панели
            if hasattr(ui_components, 'diagnostic_panel') and ui_components.diagnostic_panel:
                diagnostic_panel = ui_components.diagnostic_panel
                logger.info("[PRIORITY] DiagnosticPanel найден и готов к работе")

        logger.info("[PRIORITY] Приоритетная логика настроена успешно")

    except Exception as e:
        logger.error(f"Ошибка настройки приоритетной логики: {e}")

def _setup_ui_panels_priority(controller, ui_components, logger):
    """ИСПРАВЛЕННАЯ настройка UI панелей с приоритетной логикой"""
    try:
        logger.info("[PRIORITY] Настройка UI панелей с приоритетной логикой...")

        # КРИТИЧНО: Установка time_panel с приоритетом
        if hasattr(ui_components, 'time_panel'):
            if hasattr(controller, 'set_time_panel'):
                controller.set_time_panel(ui_components.time_panel)
                logger.info("[PRIORITY] TimePanel установлен в контроллере с приоритетом")
            else:
                setattr(controller, 'time_panel', ui_components.time_panel)
                logger.info("[PRIORITY] TimePanel установлен как атрибут контроллера")

        # Установка filter_panel с синхронизацией
        if hasattr(ui_components, 'filter_panel'):
            if hasattr(controller, 'set_filter_panel'):
                controller.set_filter_panel(ui_components.filter_panel)
                logger.info("[PRIORITY] FilterPanel установлен в контроллере с синхронизацией")
            else:
                setattr(controller.view, 'filterpanel', ui_components.filter_panel)
                logger.info("[PRIORITY] FilterPanel установлен как атрибут view")

        # Установка parameter_panel
        if hasattr(ui_components, 'parameter_panel'):
            if hasattr(controller, 'set_parameter_panel'):
                controller.set_parameter_panel(ui_components.parameter_panel)
                logger.info("[PRIORITY] ParameterPanel установлен в контроллере")
            else:
                setattr(controller.view, 'parameterpanel', ui_components.parameter_panel)
                logger.info("[PRIORITY] ParameterPanel установлен как атрибут view")

        # Установка action_panel
        if hasattr(ui_components, 'action_panel'):
            if hasattr(controller, 'set_action_panel'):
                controller.set_action_panel(ui_components.action_panel)
                logger.info("[PRIORITY] ActionPanel установлен в контроллере")
            else:
                setattr(controller.view, 'actionpanel', ui_components.action_panel)
                logger.info("[PRIORITY] ActionPanel установлен как атрибут view")

        # НОВОЕ: Установка diagnostic_panel
        if hasattr(ui_components, 'diagnostic_panel'):
            if hasattr(controller, 'set_diagnostic_panel'):
                controller.set_diagnostic_panel(ui_components.diagnostic_panel)
                logger.info("[PRIORITY] DiagnosticPanel установлен в контроллере")
            else:
                setattr(controller, 'diagnostic_panel', ui_components.diagnostic_panel)
                logger.info("[PRIORITY] DiagnosticPanel установлен как атрибут контроллера")

        logger.info("[PRIORITY] Все UI панели настроены с приоритетной логикой")

    except Exception as e:
        logger.error(f"Ошибка настройки UI панелей: {e}")

def _debug_priority_setup(main_controller, main_window, logger):
    """НОВАЯ функция отладки приоритетной настройки"""
    try:
        logger.info("=== ОТЛАДКА ПРИОРИТЕТНОЙ ЛОГИКИ ===")
        
        # Проверяем контроллер
        logger.info(f"MainController тип: {type(main_controller)}")
        
        # Проверяем методы приоритетной логики в контроллере
        priority_methods = [
            'apply_changed_parameters_filter',
            'get_ui_component',
            'apply_filters',
            '_update_parameter_display',
            '_matches_system_filter'
        ]
        
        for method_name in priority_methods:
            if hasattr(main_controller, method_name):
                logger.info(f"[PRIORITY] MainController имеет метод: {method_name}")
            else:
                logger.warning(f"[PRIORITY] MainController НЕ имеет метод: {method_name}")

        # Проверяем UI компоненты
        if hasattr(main_window, 'ui_components'):
            ui_components = main_window.ui_components
            logger.info(f"UIComponents тип: {type(ui_components)}")
            
            # Проверяем каждый компонент
            components_to_check = ['time_panel', 'filter_panel', 'parameter_panel', 'action_panel', 'diagnostic_panel']
            
            for comp_name in components_to_check:
                if hasattr(ui_components, comp_name):
                    comp = getattr(ui_components, comp_name)
                    if comp:
                        logger.info(f"[PRIORITY] {comp_name} доступен: {type(comp)}")
                        
                        # Проверяем приоритетные методы
                        if comp_name == 'time_panel':
                            priority_methods = ['set_changed_params_priority', 'get_filter_settings']
                            for method in priority_methods:
                                if hasattr(comp, method):
                                    logger.info(f"[PRIORITY] {comp_name} имеет метод: {method}")
                                else:
                                    logger.warning(f"[PRIORITY] {comp_name} НЕ имеет метод: {method}")
                        
                        elif comp_name == 'filter_panel':
                            sync_methods = ['disable_changed_only_checkbox', '_sync_with_time_panel']
                            for method in sync_methods:
                                if hasattr(comp, method):
                                    logger.info(f"[PRIORITY] {comp_name} имеет метод: {method}")
                                else:
                                    logger.warning(f"[PRIORITY] {comp_name} НЕ имеет метод: {method}")
                    else:
                        logger.warning(f"[PRIORITY] {comp_name} равен None")
                else:
                    logger.warning(f"[PRIORITY] {comp_name} НЕ найден в ui_components")

        # Проверяем модель данных
        if hasattr(main_controller, 'model'):
            model = main_controller.model
            logger.info(f"DataModel тип: {type(model)}")
            
            # Проверяем приоритетные методы модели
            model_priority_methods = [
                'find_changed_parameters_in_range',
                'set_priority_mode',
                'get_time_range_fields'
            ]
            
            for method_name in model_priority_methods:
                if hasattr(model, method_name):
                    logger.info(f"[PRIORITY] DataModel имеет метод: {method_name}")
                else:
                    logger.warning(f"[PRIORITY] DataModel НЕ имеет метод: {method_name}")

        logger.info("=== КОНЕЦ ОТЛАДКИ ПРИОРИТЕТНОЙ ЛОГИКИ ===")
        
    except Exception as e:
        logger.error(f"Ошибка отладки приоритетной логики: {e}")

def _run_application(app_context, logger):
    """Запуск приложения с приоритетной логикой"""
    try:
        logger.info("[PRIORITY] Приложение инициализировано с приоритетной логикой изменяемых параметров")
        logger.info("Для использования приоритетной логики:")
        logger.info("1. Загрузите CSV файл")
        logger.info("2. Используйте чекбокс 'Только изменяемые параметры' в панели времени")
        logger.info("3. Приоритетный фильтр автоматически отключит обычные фильтры")
        
        # Показываем окно
        app_context['root'].deiconify()  # Показываем окно если оно было скрыто
        app_context['root'].lift()       # Поднимаем окно наверх
        app_context['root'].focus_force() # Даем фокус окну
        
        app_context['root'].mainloop()

    except Exception as e:
        logger.error(f"Ошибка выполнения приложения: {e}")
    finally:
        # Очистка ресурсов
        _cleanup_application(app_context, logger)

def _cleanup_application(app_context, logger):
    """Очистка ресурсов приложения с приоритетной логикой"""
    try:
        logger.info("[PRIORITY] Очистка ресурсов приложения...")

        # Очищаем контроллер
        if 'main_controller' in app_context:
            controller = app_context['main_controller']
            if hasattr(controller, 'cleanup'):
                controller.cleanup()
                logger.info("[PRIORITY] MainController очищен")

        # Очищаем UI
        if 'main_window' in app_context:
            main_window = app_context['main_window']
            if hasattr(main_window, 'cleanup'):
                main_window.cleanup()
                logger.info("[PRIORITY] MainWindow очищен")

        # Очищаем сервисы
        if 'services' in app_context:
            for service_name, service in app_context['services'].items():
                if service and hasattr(service, 'cleanup'):
                    service.cleanup()
                    logger.info(f"[PRIORITY] {service_name} очищен")

        # Очищаем модель
        if 'model' in app_context:
            model = app_context['model']
            if hasattr(model, 'cleanup'):
                model.cleanup()
                logger.info("[PRIORITY] DataModel очищен")

        logger.info("[PRIORITY] Все ресурсы приложения очищены")

    except Exception as e:
        logger.error(f"Ошибка очистки ресурсов: {e}")

if __name__ == "__main__":
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("Запуск в тестовом режиме...")
        # Можно добавить тестовый режим в будущем
    
    main()
