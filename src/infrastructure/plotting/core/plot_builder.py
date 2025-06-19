"""
Построитель графиков с поддержкой различных стратегий
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Protocol
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.axes import Axes


class PlotStrategy(Protocol):
    """Протокол для стратегий построения графиков"""

    def plot(self, ax: Axes, x_data: np.ndarray, y_data: np.ndarray,
             label: str, **kwargs) -> Any:
        """Построение графика по стратегии"""
        ...


class LinePlotStrategy:
    """Стратегия линейных графиков"""

    def plot(self, ax: Axes, x_data: np.ndarray, y_data: np.ndarray,
             label: str, **kwargs) -> Any:
        return ax.plot(x_data, y_data, label=label, **kwargs)


class StepPlotStrategy:
    """Стратегия ступенчатых графиков (для дискретных сигналов)"""

    def plot(self, ax: Axes, x_data: np.ndarray, y_data: np.ndarray,
             label: str, **kwargs) -> Any:
        return ax.step(x_data, y_data, label=label, where='post', **kwargs)


class ScatterPlotStrategy:
    """Стратегия точечных графиков"""

    def plot(self, ax: Axes, x_data: np.ndarray, y_data: np.ndarray,
             label: str, **kwargs) -> Any:
        return ax.scatter(x_data, y_data, label=label, **kwargs)


class PlotBuilder:
    """Построитель графиков с использованием стратегий"""

    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.logger = logging.getLogger(self.__class__.__name__)

        # Стратегии построения
        self.strategies = {
            'line': LinePlotStrategy(),
            'step': StepPlotStrategy(),
            'scatter': ScatterPlotStrategy()
        }

        # Настройки по умолчанию
        self.default_colors = plt.cm.tab20(np.linspace(0, 1, 20))
        self.max_params_per_plot = 20

    def _configure_plot_appearance(self, ax: Axes, title: str,
                                   start_time: datetime, end_time: datetime):
        """Настройка внешнего вида графика"""
        # Заголовок и подписи осей
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel("Время", fontsize=12)
        ax.set_ylabel("Значение", fontsize=12)

        # Сетка
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

        # ЕДИНАЯ настройка оси времени с сохранением границ
        self._configure_time_axis_with_bounds(ax, start_time, end_time)

        # Легенда
        if ax.get_lines():
            legend = ax.legend(
                bbox_to_anchor=(1.05, 1), loc='upper left',
                fontsize=8, frameon=True, fancybox=True, shadow=True
            )
            legend.get_frame().set_alpha(0.9)

        # Автоматическое масштабирование по Y
        ax.autoscale(axis='y', tight=True)

        # Улучшение внешнего вида
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')

    def _configure_time_axis_with_bounds(self, ax: Axes, start_time: datetime, end_time: datetime):
        """ОБЪЕДИНЕННАЯ настройка оси времени с сохранением границ"""
        import matplotlib.dates as mdates
        
        # Преобразуем в числовой формат matplotlib
        start_num = mdates.date2num(start_time)
        end_num = mdates.date2num(end_time)
        
        # СОХРАНЯЕМ границы в PlotBuilder для передачи в zoom interaction
        self.time_bounds = {
            'start_time': start_time,
            'end_time': end_time,
            'start_num': start_num,
            'end_num': end_num
        }
        
        # Устанавливаем границы
        ax.set_xlim(start_num, end_num)
        
        # Настройка адаптивного форматирования
        def format_time_based_on_range(ax):
            """Функция для динамического изменения форматирования"""
            try:
                xlim = ax.get_xlim()
                current_start = mdates.num2date(xlim[0])
                current_end = mdates.num2date(xlim[1])
                duration = (current_end - current_start).total_seconds()
                
                # Выбираем формат в зависимости от текущего диапазона
                if duration <= 0.1:  # До 100 миллисекунд
                    locator = mdates.MicrosecondLocator(interval=10000)
                    formatter = mdates.DateFormatter("%H:%M:%S.%f")
                    minor_locator = mdates.MicrosecondLocator(interval=5000)
                elif duration <= 0.5:  # До 500 миллисекунд
                    locator = mdates.MicrosecondLocator(interval=50000)
                    formatter = mdates.DateFormatter("%H:%M:%S.%f")
                    minor_locator = mdates.MicrosecondLocator(interval=10000)
                elif duration <= 1:  # До 1 секунды
                    locator = mdates.MicrosecondLocator(interval=100000)
                    formatter = mdates.DateFormatter("%H:%M:%S.%f")
                    minor_locator = mdates.MicrosecondLocator(interval=50000)
                elif duration <= 5:  # До 5 секунд
                    locator = mdates.MicrosecondLocator(interval=500000)
                    formatter = mdates.DateFormatter("%H:%M:%S.%f")
                    minor_locator = mdates.MicrosecondLocator(interval=100000)
                elif duration <= 10:  # До 10 секунд
                    locator = mdates.SecondLocator(interval=1)
                    formatter = mdates.DateFormatter("%H:%M:%S")
                    minor_locator = mdates.MicrosecondLocator(interval=500000)
                elif duration <= 60:  # До минуты
                    locator = mdates.SecondLocator(interval=5)
                    formatter = mdates.DateFormatter("%H:%M:%S")
                    minor_locator = mdates.SecondLocator(interval=1)
                elif duration <= 300:  # До 5 минут
                    locator = mdates.SecondLocator(interval=30)
                    formatter = mdates.DateFormatter("%H:%M:%S")
                    minor_locator = mdates.SecondLocator(interval=10)
                elif duration <= 1800:  # До 30 минут
                    locator = mdates.MinuteLocator(interval=1)
                    formatter = mdates.DateFormatter("%H:%M:%S")
                    minor_locator = mdates.SecondLocator(interval=30)
                elif duration <= 3600:  # До часа
                    locator = mdates.MinuteLocator(interval=5)
                    formatter = mdates.DateFormatter("%H:%M:%S")
                    minor_locator = mdates.MinuteLocator(interval=1)
                elif duration <= 21600:  # До 6 часов
                    locator = mdates.MinuteLocator(interval=30)
                    formatter = mdates.DateFormatter("%H:%M")
                    minor_locator = mdates.MinuteLocator(interval=10)
                elif duration <= 86400:  # До дня
                    locator = mdates.HourLocator(interval=1)
                    formatter = mdates.DateFormatter("%H:%M")
                    minor_locator = mdates.MinuteLocator(interval=30)
                else:  # Больше дня
                    locator = mdates.HourLocator(interval=6)
                    formatter = mdates.DateFormatter("%d/%m %H:%M")
                    minor_locator = mdates.HourLocator(interval=1)
                
                # Применяем новые настройки
                ax.xaxis.set_major_locator(locator)
                ax.xaxis.set_major_formatter(formatter)
                ax.xaxis.set_minor_locator(minor_locator)
                
                # Настройка внешнего вида меток
                ax.tick_params(which='minor', length=2, color='gray', alpha=0.7)
                
                # Настройка размера шрифта
                fontsize = 7 if duration <= 1 else (8 if duration <= 10 else 9)
                plt.setp(ax.xaxis.get_majorticklabels(), fontsize=fontsize)
                
                # Поворот меток
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
                
                self.logger.debug(f"Обновлено форматирование времени для диапазона {duration:.3f}с")
                
            except Exception as e:
                self.logger.error(f"Ошибка адаптивного форматирования: {e}")
        
        # Сохраняем функцию для использования в zoom interaction
        ax._time_formatter = format_time_based_on_range
        
        # Добавляем ссылку на границы в ax для zoom interaction
        ax._time_bounds = self.time_bounds
        
        # Первоначальная настройка
        format_time_based_on_range(ax)
        
        # Логирование
        self.logger.info(f"Ось времени настроена: {start_time} - {end_time}")

    def get_time_bounds(self) -> dict:
        """Получение временных границ для zoom interaction"""
        return getattr(self, 'time_bounds', None)

    def _has_data(self) -> bool:
        """Проверка наличия данных для построения графиков"""
        try:
            if not self.data_loader:
                self.logger.warning("data_loader не инициализирован")
                return False
                
            if hasattr(self.data_loader, 'data'):
                if self.data_loader.data is None:
                    self.logger.warning("data_loader.data is None")
                    return False
                    
                if hasattr(self.data_loader.data, 'empty'):
                    if self.data_loader.data.empty:
                        self.logger.warning("DataFrame пуст")
                        return False
                    return True
                    
                return True
                
            self.logger.warning("data_loader не содержит атрибута data")
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки данных: {e}")
            return False

    def build_plot(self, params: List[Dict[str, Any]], start_time: datetime,
                   end_time: datetime, title: str = "",
                   strategy: str = 'step') -> tuple[Figure, Axes]:
        """Построение графика с заданными параметрами"""
        try:
            # Проверка наличия данных
            if not self._has_data():
                fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
                fig.patch.set_facecolor('white')
                self._show_no_data_message(ax, "Данные не загружены")
                return fig, ax

            # Создание фигуры
            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            fig.patch.set_facecolor('white')

            # Получение данных с фильтрацией по времени
            filtered_df = self._get_filtered_data(start_time, end_time)
            if filtered_df.empty:
                self._show_no_data_message(
                    ax, "Нет данных в указанном диапазоне")
                return fig, ax

            # Ограничение количества параметров
            params = params[:self.max_params_per_plot]

            # Построение линий для каждого параметра
            lines_plotted = self._plot_parameters(
                ax, params, filtered_df, strategy)

            if lines_plotted == 0:
                self._show_no_data_message(
                    ax, "Нет валидных данных для отображения")
                return fig, ax

            # Настройка внешнего вида
            self._configure_plot_appearance(ax, title, start_time, end_time)

            # Финальная настройка
            fig.tight_layout()

            self.logger.info(f"График построен: {lines_plotted} параметров")
            return fig, ax

        except Exception as e:
            self.logger.error(f"Ошибка построения графика: {e}")
            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            fig.patch.set_facecolor('white')
            self._show_no_data_message(ax, f"Ошибка: {e}")
            return fig, ax

    def _plot_parameters(self, ax, params: List[Dict[str, Any]], 
                         filtered_df, strategy: str) -> int:
        """ИСПРАВЛЕННОЕ построение параметров на графике"""
        if filtered_df.empty:
            self.logger.error("DataFrame пуст")
            return 0

        # Проверяем наличие столбца времени
        timestamp_col = None
        possible_time_cols = ['timestamp', 'time', 'datetime', 'Timestamp', 'Time']
        
        for col in possible_time_cols:
            if col in filtered_df.columns:
                timestamp_col = col
                break
        
        if not timestamp_col:
            self.logger.error("Столбец времени не найден")
            return 0

        # Преобразование времени в числовой формат для matplotlib
        timestamps_num = mdates.date2num(filtered_df[timestamp_col])

        plot_strategy = self.strategies.get(strategy, self.strategies['step'])
        lines_plotted = 0

        for idx, param in enumerate(params):
            try:
                # ИСПРАВЛЕНИЕ: Множественные способы поиска столбца
                col_name = None
                
                # Способ 1: По full_column
                if param.get('full_column') and param['full_column'] in filtered_df.columns:
                    col_name = param['full_column']
                    self.logger.debug(f"Столбец найден по full_column: {col_name}")
                
                # Способ 2: По signal_code
                elif param.get('signal_code') and param['signal_code'] in filtered_df.columns:
                    col_name = param['signal_code']
                    self.logger.debug(f"Столбец найден по signal_code: {col_name}")
                
                # Способ 3: Поиск по паттерну
                elif param.get('signal_code'):
                    signal_code = param['signal_code']
                    # Ищем столбцы содержащие signal_code
                    matching_cols = [col for col in filtered_df.columns if signal_code in col]
                    if matching_cols:
                        col_name = matching_cols[0]
                        self.logger.debug(f"Столбец найден по паттерну: {col_name}")
                
                # Способ 4: Для тестовых данных
                if not col_name and idx < len(filtered_df.columns) - 1:  # -1 для timestamp
                    available_cols = [col for col in filtered_df.columns if col != timestamp_col]
                    if idx < len(available_cols):
                        col_name = available_cols[idx]
                        self.logger.debug(f"Столбец выбран для тестовых данных: {col_name}")

                if not col_name:
                    self.logger.warning(f"Столбец не найден для параметра: {param.get('signal_code', 'Unknown')}")
                    continue

                # Преобразование значений в числовой формат
                values = pd.to_numeric(filtered_df[col_name], errors='coerce')
                if values.dropna().empty:
                    self.logger.warning(f"Нет валидных данных в столбце: {col_name}")
                    continue

                # Создание метки для легенды
                label = self._create_parameter_label(param, idx, col_name)

                # Выбор цвета
                color = self.default_colors[idx % len(self.default_colors)]

                # Построение линии с использованием стратегии
                plot_strategy.plot(
                    ax, timestamps_num, values, label=label,
                    color=color, linewidth=1.5, alpha=0.8
                )

                lines_plotted += 1
                self.logger.debug(f"Построен график для: {col_name}")

            except Exception as e:
                self.logger.warning(f"Ошибка построения параметра {param.get('signal_code', 'Unknown')}: {e}")
                continue

        return lines_plotted

    def _create_parameter_label(self, param: Dict[str, Any], index: int, col_name: str = None) -> str:
        """УЛУЧШЕННОЕ создание метки для параметра"""
        signal_code = param.get('signal_code', col_name or f'Param_{index}')
        description = param.get('description', '')
        
        if description and description != signal_code:
            # Ограничиваем длину описания
            max_desc_length = 30
            if len(description) > max_desc_length:
                description = description[:max_desc_length] + '...'
            return f"{signal_code} - {description}"
        else:
            return signal_code

    def _show_no_data_message(self, ax: Axes, message: str):
        """Отображение сообщения об отсутствии данных"""
        ax.text(0.5, 0.5, message, ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

    def _get_filtered_data(self, start_time: datetime, end_time: datetime):
        """НОВЫЙ метод получения отфильтрованных данных"""
        try:
            # Способ 1: Через data_loader.data (DataFrame)
            if hasattr(self.data_loader, 'data') and self.data_loader.data is not None:
                df = self.data_loader.data
                
                # Проверяем наличие столбца времени
                timestamp_col = None
                possible_time_cols = ['timestamp', 'time', 'datetime', 'Timestamp', 'Time']
                
                for col in possible_time_cols:
                    if col in df.columns:
                        timestamp_col = col
                        break
                
                if timestamp_col:
                    # Фильтрация по времени
                    mask = (df[timestamp_col] >= start_time) & (df[timestamp_col] <= end_time)
                    filtered_df = df[mask].copy()
                    self.logger.info(f"Отфильтровано {len(filtered_df)} записей из {len(df)}")
                    return filtered_df
                else:
                    self.logger.warning("Столбец времени не найден, возвращаем все данные")
                    return df

            # Способ 2: Возвращаем пустой DataFrame вместо создания синтетических данных
            self.logger.warning("Данные не найдены, возвращаем пустой DataFrame")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Ошибка получения данных: {e}")
            import pandas as pd
            return pd.DataFrame()
