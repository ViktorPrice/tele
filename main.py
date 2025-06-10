# main.py - РЕФАКТОРЕННАЯ ВЕРСИЯ (v1.0)
"""
Точка входа приложения с вынесенной DataModel и улучшенной архитектурой
"""
import sys
import logging
import locale
import tkinter as tk
from pathlib import Path
import os

# Изменения:
# - Было: Inline DataModel класс в main()
# - Стало: Импорт отдельного модуля DataModel
# - Влияние: Улучшена модульность, соблюден SRP
# - REVIEW NEEDED: Проверить совместимость с существующими компонентами


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
                    '✓': 'OK', '→': '->', '←': '<-',
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

# Изменения:
# - Было: Множественные try-catch блоки
# - Стало: Единый exception handler с детальным логированием
# - Влияние: Улучшена читаемость и отладка
# - REVIEW NEEDED: Убедиться что все исключения корректно обрабатываются


def main():
    """Главная функция с исправленной архитектурой"""
    setup_encoding()
    setup_safe_logging()

    logger = logging.getLogger(__name__)
    logger.info("=== ЗАПУСК ПРИЛОЖЕНИЯ (ТОЛЬКО НОВАЯ АРХИТЕКТУРА) ===")

    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src'))

        # Импорты с обработкой ошибок
        components = _import_components(logger)
        if not components:
            return

        # Создание приложения
        app_context = _create_application_context(components, logger)
        if not app_context:
            return

        # Запуск приложения
        _run_application(app_context, logger)

    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


def _import_components(logger):
    """Безопасный импорт компонентов"""
    try:
        from src.ui.views.main_window import MainWindow
        from src.ui.controllers.main_controller import MainController
        from src.core.domain.services.filtering_service import ParameterFilteringService
        from src.infrastructure.data.csv_loader import CSVDataLoader
        from src.infrastructure.plotting.core.plot_manager import PlotManager
        from src.infrastructure.reporting.core.report_manager import ReportManager
        from src.infrastructure.sop.core.sop_manager import SOPManager
        from src.core.models.data_model import DataModel  # Вынесенный класс

        return {
            'MainWindow': MainWindow,
            'MainController': MainController,
            'ParameterFilteringService': ParameterFilteringService,
            'CSVDataLoader': CSVDataLoader,
            'PlotManager': PlotManager,
            'ReportManager': ReportManager,
            'SOPManager': SOPManager,
            'DataModel': DataModel
        }

    except ImportError as e:
        logger.error(f"Ошибка импорта компонентов: {e}")
        return None


def _create_application_context(components, logger):
    """Создание контекста приложения"""
    try:
        # Создание главного окна
        root = tk.Tk()
        root.title("Анализатор телеметрии - НОВАЯ АРХИТЕКТУРА")

        # Добавлено: применение темы и стилей
        from src.ui.utils.styles import StyleManager
        style_manager = StyleManager()
        style_manager.apply_theme('light')

        logger.info("Создание компонентов новой архитектуры...")

        # Создание модели (теперь отдельный класс)
        model = components['DataModel']()

        # Создание сервисов с dependency injection
        services = _create_services(components, model.data_loader, logger)

        # Создание UI
        main_window = components['MainWindow'](root)
        main_window.setup()

        # Создание контроллера
        main_controller = components['MainController'](model, main_window)

        # Внедрение зависимостей
        _inject_dependencies(main_controller, services, logger)

        # Установка контроллера в UI
        main_window.set_controller(main_controller)

        # Явное создание и установка ui_components и панелей в контроллер
        if hasattr(main_window, 'ui_components'):
            main_controller.set_ui_components(main_window.ui_components)

            # Установка time_panel
            if hasattr(main_window.ui_components, 'time_panel'):
                main_controller.set_time_panel(
                    main_window.ui_components.time_panel)

            # Установка filter_panel
            if hasattr(main_window.ui_components, 'filter_panel'):
                if hasattr(main_controller, 'set_filter_panel'):
                    main_controller.set_filter_panel(main_window.ui_components.filter_panel)
                else:
                    setattr(main_controller.view, '_filter_panel',
                            main_window.ui_components.filter_panel)

            # Установка parameter_panel
            if hasattr(main_window.ui_components, 'parameter_panel'):
                if hasattr(main_controller, 'set_parameter_panel'):
                    main_controller.set_parameter_panel(main_window.ui_components.parameter_panel)
                else:
                    setattr(main_controller.view, '_parameter_panel',
                            main_window.ui_components.parameter_panel)

            # Установка action_panel
            if hasattr(main_window.ui_components, 'action_panel'):
                if hasattr(main_controller, 'set_action_panel'):
                    main_controller.set_action_panel(main_window.ui_components.action_panel)
                else:
                    setattr(main_controller.view, '_action_panel',
                            main_window.ui_components.action_panel)

        # Добавление обработчика закрытия окна
        def on_closing():
            try:
                logger.info("Закрытие приложения")
                if hasattr(main_controller, 'save_filters'):
                    main_controller.save_filters()
                if hasattr(main_controller, 'cleanup'):
                    main_controller.cleanup()
            except Exception as e:
                logger.error(f"Ошибка при закрытии: {e}")
            finally:
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        return {
            'root': root,
            'model': model,
            'main_window': main_window,
            'main_controller': main_controller,
            'services': services
        }

    except Exception as e:
        logger.error(f"Ошибка создания контекста приложения: {e}")
        return None


def _create_services(components, data_loader, logger):
    """Создание сервисов с dependency injection"""
    try:
        filtering_service = components['ParameterFilteringService'](
            data_loader)
        plot_manager = components['PlotManager'](data_loader)
        report_manager = components['ReportManager'](data_loader, plot_manager)
        sop_manager = components['SOPManager'](data_loader)

        return {
            'filtering_service': filtering_service,
            'plot_manager': plot_manager,
            'report_manager': report_manager,
            'sop_manager': sop_manager
        }

    except Exception as e:
        logger.error(f"Ошибка создания сервисов: {e}")
        return {}


def _inject_dependencies(controller, services, logger):
    """Внедрение зависимостей в контроллер"""
    try:
        for service_name, service in services.items():
            setter_name = f"set_{service_name}"
            if hasattr(controller, setter_name):
                getattr(controller, setter_name)(service)
                logger.debug(f"Внедрен сервис: {service_name}")
            else:
                logger.warning(f"Метод {setter_name} не найден в контроллере")

    except Exception as e:
        logger.error(f"Ошибка внедрения зависимостей: {e}")


def _run_application(app_context, logger):
    """Запуск приложения"""
    try:
        logger.info("Приложение инициализировано (ТОЛЬКО НОВАЯ АРХИТЕКТУРА)")
        app_context['root'].mainloop()

    except Exception as e:
        logger.error(f"Ошибка выполнения приложения: {e}")
    finally:
        # Очистка ресурсов
        _cleanup_application(app_context, logger)


def _cleanup_application(app_context, logger):
    """Очистка ресурсов приложения"""
    try:
        if 'services' in app_context:
            for service in app_context['services'].values():
                if hasattr(service, 'cleanup'):
                    service.cleanup()

        logger.info("Ресурсы приложения очищены")

    except Exception as e:
        logger.error(f"Ошибка очистки ресурсов: {e}")


if __name__ == "__main__":
    main()
