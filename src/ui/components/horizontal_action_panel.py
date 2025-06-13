# src/ui/components/horizontal_action_panel.py - ПОЛНАЯ ВЕРСИЯ
"""
Горизонтальная панель действий в одну строку без дублирования функционала
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional

class HorizontalActionPanel(ttk.Frame):
    """Горизонтальная панель действий без дублирования логики"""

    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # UI элементы
        self.buttons = {}
        
        self._setup_horizontal_ui()
        self.logger.info("HorizontalActionPanel инициализирован")

    def _setup_horizontal_ui(self):
        """Настройка горизонтального UI без дублирования"""
        try:
            # Конфигурация сетки
            for i in range(4):
                self.grid_columnconfigure(i, weight=1)

            # Определение кнопок без дублирования функционала
            buttons_config = [
                ("📊 Построить график", self._build_plot, "Построение графиков выбранных параметров"),
                ("📄 Создать отчет", self._generate_report, "Генерация отчета по данным"),
                ("📋 Создать SOP", self._generate_sop, "Создание стандартной операционной процедуры"),
                ("🧪 Тест данных", self._load_test_data, "Загрузка тестовых данных")
            ]

            # Создание кнопок
            for i, (text, command, tooltip) in enumerate(buttons_config):
                btn = ttk.Button(
                    self, 
                    text=text, 
                    command=command, 
                    width=18
                )
                btn.grid(row=0, column=i, padx=3, pady=5, sticky="ew")
                
                # Сохраняем ссылку на кнопку
                action_key = text.split()[1].lower()  # Извлекаем ключевое слово
                self.buttons[action_key] = btn
                
                # Добавляем tooltip (подсказку)
                self._create_tooltip(btn, tooltip)

            self.logger.info("UI горизонтальной панели действий создан")

        except Exception as e:
            self.logger.error(f"Ошибка создания UI панели действий: {e}")

    def _create_tooltip(self, widget, text):
        """Создание подсказки для виджета"""
        def on_enter(event):
            try:
                # Простая реализация tooltip
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                label = tk.Label(
                    tooltip, 
                    text=text, 
                    background="lightyellow",
                    relief="solid",
                    borderwidth=1,
                    font=("Arial", 8)
                )
                label.pack()
                
                widget.tooltip = tooltip
            except Exception:
                pass

        def on_leave(event):
            try:
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
                    delattr(widget, 'tooltip')
            except Exception:
                pass

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _build_plot(self):
        """Построение графика без дублирования логики"""
        try:
            if self.controller and hasattr(self.controller, 'build_plot'):
                self.controller.build_plot()
                self.logger.info("Запрос на построение графика отправлен контроллеру")
            else:
                self.logger.warning("Контроллер не поддерживает построение графиков")
                self._show_not_implemented("Построение графиков")
        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")

    def _generate_report(self):
        """Генерация отчета без дублирования логики"""
        try:
            if self.controller and hasattr(self.controller, 'generate_report'):
                self.controller.generate_report()
                self.logger.info("Запрос на генерацию отчета отправлен контроллеру")
            else:
                self.logger.warning("Контроллер не поддерживает генерацию отчетов")
                self._show_not_implemented("Генерация отчетов")
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета: {e}")

    def _generate_sop(self):
        """Создание SOP без дублирования логики"""
        try:
            if self.controller and hasattr(self.controller, 'generate_sop'):
                self.controller.generate_sop()
                self.logger.info("Запрос на создание SOP отправлен контроллеру")
            else:
                self.logger.warning("Контроллер не поддерживает создание SOP")
                self._show_not_implemented("Создание SOP")
        except Exception as e:
            self.logger.error(f"Ошибка создания SOP: {e}")

    def _load_test_data(self):
        """Загрузка тестовых данных без дублирования логики"""
        try:
            if self.controller and hasattr(self.controller, 'load_test_data'):
                self.controller.load_test_data()
                self.logger.info("Запрос на загрузку тестовых данных отправлен контроллеру")
            else:
                self.logger.warning("Контроллер не поддерживает загрузку тестовых данных")
                self._show_not_implemented("Загрузка тестовых данных")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки тестовых данных: {e}")

    def _show_not_implemented(self, feature_name: str):
        """Показ сообщения о нереализованной функции"""
        try:
            import tkinter.messagebox as msgbox
            msgbox.showinfo(
                "Информация", 
                f"{feature_name} пока не реализована.\nБудет добавлена в следующих версиях."
            )
        except Exception as e:
            self.logger.error(f"Ошибка показа сообщения: {e}")

    def set_button_state(self, button_key: str, state: str):
        """Установка состояния кнопки"""
        try:
            if button_key in self.buttons:
                self.buttons[button_key].config(state=state)
                self.logger.debug(f"Состояние кнопки '{button_key}' изменено на '{state}'")
            else:
                self.logger.warning(f"Кнопка '{button_key}' не найдена")
        except Exception as e:
            self.logger.error(f"Ошибка установки состояния кнопки: {e}")

    def enable_all_buttons(self):
        """Включение всех кнопок"""
        try:
            for button in self.buttons.values():
                button.config(state='normal')
            self.logger.info("Все кнопки включены")
        except Exception as e:
            self.logger.error(f"Ошибка включения кнопок: {e}")

    def disable_all_buttons(self):
        """Отключение всех кнопок"""
        try:
            for button in self.buttons.values():
                button.config(state='disabled')
            self.logger.info("Все кнопки отключены")
        except Exception as e:
            self.logger.error(f"Ошибка отключения кнопок: {e}")

    def set_controller(self, controller):
        """Установка контроллера"""
        self.controller = controller
        self.logger.info("✅ Контроллер установлен в HorizontalActionPanel")

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.controller = None
            self.buttons.clear()
            self.logger.info("HorizontalActionPanel очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки HorizontalActionPanel: {e}")

    def get_status_info(self) -> dict:
        """Получение информации о состоянии панели"""
        try:
            return {
                'total_buttons': len(self.buttons),
                'enabled_buttons': len([b for b in self.buttons.values() if str(b['state']) == 'normal']),
                'controller_available': self.controller is not None,
                'buttons': list(self.buttons.keys())
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о состоянии: {e}")
            return {}

    def __str__(self):
        return f"HorizontalActionPanel(buttons={len(self.buttons)}, controller={'set' if self.controller else 'none'})"

    def __repr__(self):
        return self.__str__()
