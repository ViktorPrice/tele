import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class DataLoaderController:
    """Контроллер для загрузки и обработки данных (CSV, передача данных в модель)"""

    def __init__(self, model, view, event_emitter):
        self.model = model
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_emitter = event_emitter  # Функция или объект для эмиссии событий
        self.is_loading = False
        self.current_file_path: Optional[str] = None

    def upload_csv(self):
        """Загрузка CSV файла через диалог выбора"""
        try:
            from tkinter import filedialog

            file_path = filedialog.askopenfilename(
                title="Выберите CSV файл",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            )

            if file_path:
                self.load_csv_file(file_path)
            else:
                self.logger.info("Загрузка файла отменена пользователем")

        except Exception as e:
            self.logger.error(f"Ошибка выбора CSV файла: {e}")
            if hasattr(self.view, "show_error"):
                self.view.show_error(f"Ошибка выбора файла: {e}")

    def load_csv_file(self, file_path: str):
        """Загрузка CSV файла"""
        try:
            self.logger.info(f"Начало загрузки CSV файла: {file_path}")

            if self.is_loading:
                self.logger.warning("Загрузка уже выполняется")
                return

            self._start_loading("Загрузка CSV файла...")
            self.current_file_path = file_path

            def load_file():
                try:
                    success = self._load_csv_file(file_path)
                    if hasattr(self.view, "root"):
                        self.view.root.after(
                            0, lambda: self._handle_file_load_result(success, file_path)
                        )
                except Exception as e:
                    self.logger.error(f"Ошибка в потоке загрузки: {e}")
                    if hasattr(self.view, "root"):
                        self.view.root.after(0, lambda: self._handle_file_load_error(e))

            thread = threading.Thread(target=load_file, daemon=True)
            thread.start()

        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV файла: {e}")
            self._stop_loading()

    def _load_csv_file(self, file_path: str) -> bool:
        """Внутренний метод загрузки CSV файла"""
        try:
            # Проверяем существование файла
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Файл не найден: {file_path}")

            # Загружаем через модель
            if hasattr(self.model, "load_csv"):
                success = self.model.load_csv(file_path)
            elif hasattr(self.model, "data_loader") and hasattr(
                self.model.data_loader, "load_csv"
            ):
                success = self.model.data_loader.load_csv(file_path)
            else:
                raise AttributeError("Модель не поддерживает загрузку CSV")

            if success:
                self.logger.info(f"CSV файл успешно загружен: {file_path}")
                return True
            else:
                self.logger.error(f"Не удалось загрузить CSV файл: {file_path}")
                return False

        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV файла {file_path}: {e}")
            raise

    def _handle_file_load_result(self, success: bool, file_path: str):
        """Обработка результата загрузки файла с передачей данных в DataModel"""
        try:
            self._stop_loading()

            if success:
                self.logger.info(f"Файл успешно загружен: {file_path}")

                # Получаем количество записей и параметров
                all_params = self._get_all_parameters()
                params_count = len(all_params)

                # Извлекаем МЦД информацию
                mcd_info = None
                if hasattr(self.model, "data_loader") and self.model.data_loader:
                    mcd_info = self.model.data_loader.extract_and_update_mcd_info(
                        file_path
                    )
                    self.logger.info(f"МЦД информация из data_loader: {mcd_info}")

                # Обновляем SmartFilterPanel с правильным ведущим вагоном
                filter_panel = None
                if hasattr(self.view, "get_component"):
                    filter_panel = self.view.get_component("filter_panel")
                if not filter_panel and hasattr(self.view, "filter_panel"):
                    filter_panel = self.view.filter_panel

                if filter_panel and mcd_info and mcd_info.get("leading_unit"):
                    try:
                        leading_unit = int(mcd_info["leading_unit"])

                        # Принудительно обновляем ведущий вагон и маппинг
                        if hasattr(filter_panel, "leading_wagon"):
                            filter_panel.leading_wagon = leading_unit
                        if hasattr(filter_panel, "_create_wagon_mapping"):
                            filter_panel._create_wagon_mapping(leading_unit)

                        # Извлекаем реальные номера вагонов из данных
                        real_wagons = list(
                            set(str(param.get("wagon", "")) for param in all_params)
                        )
                        real_wagons = [
                            wagon for wagon in real_wagons if wagon and wagon != "Unknown"
                        ]

                        # Обновляем filter_panel с реальными данными о вагонах
                        if hasattr(filter_panel, "update_wagon_checkboxes"):
                            filter_panel.update_wagon_checkboxes(real_wagons)
                            self.logger.info(
                                f"Вагоны обновлены в SmartFilterPanel: {real_wagons}"
                            )

                        self.logger.info(
                            f"SmartFilterPanel синхронизирован с ведущим вагоном: {leading_unit}"
                        )
                        if hasattr(filter_panel, "wagon_mapping"):
                            self.logger.info(f"Маппинг вагонов: {filter_panel.wagon_mapping}")

                    except ValueError:
                        self.logger.error(
                            f"Неверный формат ведущего вагона: {mcd_info['leading_unit']}"
                        )

                # Обновляем панель с МЦД данными
                file_name = Path(file_path).name
                if mcd_info and hasattr(self.view, "update_telemetry_info"):
                    self.view.update_telemetry_info(
                        file_name=file_name,
                        params_count=params_count,
                        selected_count=0,
                        line_mcd=mcd_info.get("line_mcd", ""),
                        route=mcd_info.get("route", ""),
                        train=mcd_info.get("train", ""),
                        leading_unit=mcd_info.get("leading_unit", ""),
                    )
                    self.logger.info(f"Панель обновлена с МЦД: {mcd_info}")

                # Обновляем UI после загрузки
                self._update_ui_after_data_load()

                # Принудительно обновляем интерфейс
                if hasattr(self.view, "root"):
                    self.view.root.update_idletasks()

                # Эмитируем событие загрузки данных
            if self.event_emitter and callable(self.event_emitter):
                self.event_emitter(
                    "data_loaded",
                    {
                        "file_path": file_path,
                        "params_count": params_count,
                        "mcd_info": mcd_info,
                        "timestamp": datetime.now(),
                    },
                )

                if hasattr(self.view, "show_info"):
                    self.view.show_info(
                        "Загрузка", f"Файл загружен: {Path(file_path).name}"
                    )

            else:
                self.logger.error(f"Не удалось загрузить файл: {file_path}")
                if hasattr(self.view, "show_error"):
                    self.view.show_error(
                        f"Не удалось загрузить файл: {Path(file_path).name}"
                    )

        except Exception as e:
            self.logger.error(f"Ошибка обработки результата загрузки: {e}")

    def _handle_file_load_error(self, error: Exception):
        """Обработка ошибки загрузки файла"""
        try:
            self._stop_loading()
            self.logger.error(f"Ошибка загрузки файла: {error}")

            if hasattr(self.view, "show_error"):
                self.view.show_error(f"Ошибка загрузки файла: {error}")

        except Exception as e:
            self.logger.error(f"Ошибка обработки ошибки загрузки: {e}")

    def _update_ui_after_data_load(self):
        """Обновление UI после загрузки данных"""
        try:
            self.logger.info("Начало обновления UI после загрузки данных")
            
            # Загружаем все параметры
            all_params = self._get_all_parameters()
            self.logger.info(f"Получено параметров: {len(all_params)}")

            # 1. Обновляем временную панель
            self._update_time_panel()

            # 2. Обновляем панель параметров
            self._update_parameters_panel(all_params)

            # 3. Обновляем SmartFilterPanel с данными из CSV
            self._update_smart_filter_panel_with_data(all_params)

            # 4. Обновляем UI компоненты через view
            self._update_view_components(all_params)

            # 5. Эмитируем событие обновления параметров
            if hasattr(self, 'event_emitter') and self.event_emitter:
                try:
                    self.event_emitter("parameters_updated", {"parameters": all_params})
                    self.logger.info("Событие parameters_updated эмитировано")
                except Exception as e:
                    self.logger.error(f"Ошибка эмиссии события parameters_updated: {e}")

            # 6. Принудительное обновление реестра UI
            self._refresh_ui_registry()

            self.logger.info(f"UI успешно обновлен после загрузки данных: {len(all_params)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка обновления UI после загрузки: {e}")
            import traceback
            traceback.print_exc()

    def _update_time_panel(self):
        """Обновление временной панели после загрузки данных"""
        try:
            # Получаем временной диапазон из данных
            time_range = self._get_data_time_range()
            if not time_range:
                self.logger.warning("Не удалось получить временной диапазон из данных")
                return

            start_time, end_time = time_range
            self.logger.info(f"Временной диапазон данных: {start_time} - {end_time}")

            # Получаем количество записей
            total_records = 0
            if hasattr(self.model, 'data_loader') and self.model.data_loader:
                if hasattr(self.model.data_loader, 'data') and self.model.data_loader.data is not None:
                    total_records = len(self.model.data_loader.data)

            # Обновляем временную панель через view (CompactTimePanel)
            time_panel = None
            if hasattr(self.view, 'get_component'):
                time_panel = self.view.get_component('time_panel')
            
            if not time_panel and hasattr(self.view, 'time_panel'):
                time_panel = self.view.time_panel

            if time_panel:
                # Используем правильный метод для CompactTimePanel
                if hasattr(time_panel, 'update_time_fields'):
                    time_panel.update_time_fields(start_time, end_time, total_records=total_records)
                    self.logger.info("Временная панель обновлена через update_time_fields")
                elif hasattr(time_panel, 'update_time_range'):
                    time_panel.update_time_range(start_time, end_time)
                    self.logger.info("Временная панель обновлена через update_time_range")
                else:
                    self.logger.warning("Временная панель не поддерживает update_time_fields или update_time_range")
            else:
                self.logger.warning("Временная панель не найдена")

            # Дополнительно обновляем через ui_components
            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                if hasattr(self.view.ui_components, 'time_panel'):
                    ui_time_panel = self.view.ui_components.time_panel
                    if ui_time_panel and hasattr(ui_time_panel, 'update_time_fields'):
                        ui_time_panel.update_time_fields(start_time, end_time, total_records=total_records)
                        self.logger.info("Временная панель обновлена через ui_components")

        except Exception as e:
            self.logger.error(f"Ошибка обновления временной панели: {e}")
            import traceback
            traceback.print_exc()

    def _update_parameters_panel(self, parameters: List[Dict[str, Any]]):
        """Обновление панели параметров"""
        try:
            # Обновляем панель параметров через view
            if hasattr(self.view, 'get_component'):
                params_panel = self.view.get_component('parameters_panel')
                if params_panel and hasattr(params_panel, 'update_parameters'):
                    params_panel.update_parameters(parameters)
                    self.logger.info("Панель параметров обновлена")

            # Альтернативный способ через прямой доступ
            if hasattr(self.view, 'parameters_panel'):
                params_panel = self.view.parameters_panel
                if params_panel and hasattr(params_panel, 'update_parameters'):
                    params_panel.update_parameters(parameters)
                    self.logger.info("Панель параметров обновлена (прямой доступ)")

            # Обновляем через filter_panel, если он содержит список параметров
            if hasattr(self.view, 'get_component'):
                filter_panel = self.view.get_component('filter_panel')
                if filter_panel and hasattr(filter_panel, 'update_parameters'):
                    filter_panel.update_parameters(parameters)
                    self.logger.info("Параметры обновлены в filter_panel")

        except Exception as e:
            self.logger.error(f"Ошибка обновления панели параметров: {e}")

    def _update_view_components(self, parameters: List[Dict[str, Any]]):
        """Обновление компонентов view"""
        try:
            # Обновляем параметры через view, если есть соответствующий метод
            if hasattr(self.view, 'update_parameters'):
                self.view.update_parameters(parameters)
                self.logger.info("Параметры обновлены через view.update_parameters")

            # Обновляем UI компоненты
            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                if hasattr(self.view.ui_components, 'update_parameters'):
                    self.view.ui_components.update_parameters(parameters)
                    self.logger.info("Параметры обновлены через ui_components")

        except Exception as e:
            self.logger.error(f"Ошибка обновления компонентов view: {e}")

    def _refresh_ui_registry(self):
        """Принудительное обновление реестра UI компонентов"""
        try:
            # Обновляем реестр UI через view
            if hasattr(self.view, 'refresh_ui_registry'):
                self.view.refresh_ui_registry()
                self.logger.info("Реестр UI обновлен через view")

            # Обновляем через ui_components
            if hasattr(self.view, 'ui_components') and self.view.ui_components:
                if hasattr(self.view.ui_components, 'refresh_ui_registry'):
                    self.view.ui_components.refresh_ui_registry()
                    self.logger.info("Реестр UI обновлен через ui_components")

            # Отложенное обновление реестра
            if hasattr(self.view, 'delayed_refresh_ui_registry'):
                self.view.delayed_refresh_ui_registry(100)
                self.logger.info("Запланировано отложенное обновление реестра UI")

        except Exception as e:
            self.logger.error(f"Ошибка обновления реестра UI: {e}")

    def _get_data_time_range(self):
        """Получение временного диапазона из загруженных данных"""
        try:
            # Пытаемся получить временной диапазон из data_loader
            if hasattr(self.model, 'data_loader') and self.model.data_loader:
                data_loader = self.model.data_loader
                
                # Проверяем наличие метода get_time_range
                if hasattr(data_loader, 'get_time_range'):
                    time_range = data_loader.get_time_range()
                    if time_range:
                        return time_range
                
                # Альтернативно, пытаемся получить из данных
                if hasattr(data_loader, 'data') and data_loader.data is not None:
                    # Если данные в формате DataFrame
                    if hasattr(data_loader.data, 'index'):
                        try:
                            min_time = data_loader.data.index.min()
                            max_time = data_loader.data.index.max()
                            return str(min_time), str(max_time)
                        except:
                            pass
                    
                    # Если есть колонка времени
                    if hasattr(data_loader.data, 'columns'):
                        time_columns = [col for col in data_loader.data.columns if 'time' in col.lower() or 'timestamp' in col.lower()]
                        if time_columns:
                            time_col = time_columns[0]
                            try:
                                min_time = data_loader.data[time_col].min()
                                max_time = data_loader.data[time_col].max()
                                return str(min_time), str(max_time)
                            except:
                                pass

            self.logger.warning("Не удалось определить временной диапазон из данных")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения временного диапазона: {e}")
            return None

    def _update_smart_filter_panel_with_data(self, parameters: List[Dict[str, Any]]):
        """Обновление SmartFilterPanel с данными из CSV"""
        try:
            # Получаем SmartFilterPanel
            filter_panel = None
            if hasattr(self.view, "get_component"):
                filter_panel = self.view.get_component("filter_panel")
            if not filter_panel and hasattr(self.view, "filter_panel"):
                filter_panel = self.view.filter_panel

            if not filter_panel:
                self.logger.warning("SmartFilterPanel не найден")
                return

            # Обновляем параметры в фильтре
            if hasattr(filter_panel, 'update_parameters'):
                filter_panel.update_parameters(parameters)
                self.logger.info("Параметры обновлены в SmartFilterPanel")

            # Обновляем статистику
            if hasattr(filter_panel, 'update_statistics'):
                filter_panel.update_statistics()
                self.logger.info("Статистика обновлена в SmartFilterPanel")

        except Exception as e:
            self.logger.error(f"Ошибка обновления SmartFilterPanel: {e}")

    def update_ui_after_data_load(self):
        """Публичный метод для обновления UI после загрузки данных"""
        self._update_ui_after_data_load()

    def _get_all_parameters(self) -> List[Dict[str, Any]]:
        """Получение всех параметров из модели"""
        try:
            if hasattr(self.model, "get_all_parameters"):
                params = self.model.get_all_parameters()
            elif hasattr(self.model, "data_loader") and hasattr(
                self.model.data_loader, "get_parameters"
            ):
                params = self.model.data_loader.get_parameters()
            else:
                self.logger.warning("Не удалось получить параметры из модели")
                return []

            if params and hasattr(params[0], "to_dict"):
                return [param.to_dict() for param in params]
            return params or []

        except Exception as e:
            self.logger.error(f"Ошибка получения всех параметров: {e}")
            return []

    def _start_loading(self, message: str = "Загрузка..."):
        """Начало индикации загрузки"""
        try:
            self.is_loading = True

            if hasattr(self.view, "ui_components") and self.view.ui_components:
                self.view.ui_components.start_processing(message)

            self.logger.debug(f"Начата загрузка: {message}")

        except Exception as e:
            self.logger.error(f"Ошибка начала загрузки: {e}")

    def _stop_loading(self):
        """Завершение индикации загрузки"""
        try:
            self.is_loading = False

            if hasattr(self.view, "ui_components") and self.view.ui_components:
                self.view.ui_components.stop_processing()

            self.logger.debug("Загрузка завершена")

        except Exception as e:
            self.logger.error(f"Ошибка завершения загрузки: {e}")
