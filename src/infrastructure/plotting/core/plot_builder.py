#src\infrastructure\plotting\core\plot_builder.py
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

    def diagnose_data_loader(self):
        """ДИАГНОСТИЧЕСКИЙ метод для отладки"""
        try:
            self.logger.info("=== ДИАГНОСТИКА DATA_LOADER ===")
            self.logger.info(f"Тип data_loader: {type(self.data_loader)}")
            
            # Проверяем атрибуты
            attrs = [attr for attr in dir(self.data_loader) if not attr.startswith('_')]
            self.logger.info(f"Доступные атрибуты: {attrs}")
            
            # Проверяем данные
            if hasattr(self.data_loader, 'data'):
                data = self.data_loader.data
                self.logger.info(f"data тип: {type(data)}")
                if hasattr(data, 'shape'):
                    self.logger.info(f"Размер данных: {data.shape}")
                if hasattr(data, 'columns'):
                    self.logger.info(f"Столбцы: {list(data.columns)[:10]}...")  # Первые 10
            
            # Проверяем параметры
            if hasattr(self.data_loader, 'parameters'):
                params = self.data_loader.parameters
                self.logger.info(f"Параметров: {len(params) if params else 0}")
                if params:
                    self.logger.info(f"Первый параметр: {params[0]}")
            
            # Проверяем методы валидации
            if hasattr(self.data_loader, 'validate_data'):
                try:
                    is_valid = self.data_loader.validate_data()
                    self.logger.info(f"validate_data(): {is_valid}")
                except Exception as e:
                    self.logger.error(f"Ошибка validate_data(): {e}")
            
            self.logger.info("=== КОНЕЦ ДИАГНОСТИКИ ===")
            
        except Exception as e:
            self.logger.error(f"Ошибка диагностики: {e}")

    def _has_data(self) -> bool:
        """ИСПРАВЛЕННАЯ проверка наличия данных"""
        try:
            # Способ 1: Проверяем через validate_data
            if hasattr(self.data_loader, 'validate_data'):
                if self.data_loader.validate_data():
                    return True

            # Способ 2: Проверяем наличие данных напрямую
            if hasattr(self.data_loader, 'data') and self.data_loader.data is not None:
                if hasattr(self.data_loader.data, 'empty'):
                    return not self.data_loader.data.empty
                return len(self.data_loader.data) > 0

            # Способ 3: Проверяем через parameters
            if hasattr(self.data_loader, 'parameters') and self.data_loader.parameters:
                return len(self.data_loader.parameters) > 0

            # Способ 4: Проверяем через records_count
            if hasattr(self.data_loader, 'records_count'):
                return self.data_loader.records_count > 0

            self.logger.warning("Не удалось определить наличие данных")
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
                
                # Способ 2: По signal_code
                elif param.get('signal_code') and param['signal_code'] in filtered_df.columns:
                    col_name = param['signal_code']
                
                # Способ 3: Поиск по паттерну
                elif param.get('signal_code'):
                    signal_code = param['signal_code']
                    # Ищем столбцы содержащие signal_code
                    matching_cols = [col for col in filtered_df.columns if signal_code in col]
                    if matching_cols:
                        col_name = matching_cols[0]
                
                # Способ 4: Для тестовых данных
                if not col_name and idx < len(filtered_df.columns) - 1:  # -1 для timestamp
                    available_cols = [col for col in filtered_df.columns if col != timestamp_col]
                    if idx < len(available_cols):
                        col_name = available_cols[idx]

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

    def _configure_plot_appearance(self, ax: Axes, title: str,
                                   start_time: datetime, end_time: datetime):
        """Настройка внешнего вида графика"""
        # Заголовок и подписи осей
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel("Время", fontsize=12)
        ax.set_ylabel("Значение", fontsize=12)

        # Сетка
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

        # Настройка оси времени
        self._configure_time_axis(ax, start_time, end_time)

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

    def _configure_time_axis(self, ax: Axes, start_time: datetime, end_time: datetime):
        """Настройка оси времени"""
        duration = (end_time - start_time).total_seconds()

        if duration <= 1:
            locator = mdates.MicrosecondLocator(interval=100000)
            formatter = mdates.DateFormatter("%H:%M:%S.%f")
        elif duration <= 10:
            locator = mdates.SecondLocator(interval=1)
            formatter = mdates.DateFormatter("%H:%M:%S")
        elif duration <= 60:
            locator = mdates.SecondLocator(interval=5)
            formatter = mdates.DateFormatter("%H:%M:%S")
        else:
            locator = mdates.AutoDateLocator()
            formatter = mdates.DateFormatter("%H:%M:%S")

        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        # Поворот меток времени
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Установка пределов времени
        ax.set_xlim(mdates.date2num(start_time), mdates.date2num(end_time))

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

            # Способ 2: Создаем синтетические данные для тестирования
            self.logger.warning("Создаем синтетические данные для тестирования")
            return self._create_synthetic_data(start_time, end_time)

        except Exception as e:
            self.logger.error(f"Ошибка получения данных: {e}")
            import pandas as pd
            return pd.DataFrame()

    def _create_synthetic_data(self, start_time: datetime, end_time: datetime):
        """Создание синтетических данных для тестирования"""
        try:
            import pandas as pd
            import numpy as np
            
            # Создаем временной ряд
            time_range = pd.date_range(start=start_time, end=end_time, freq='1S')
            
            # Создаем DataFrame с синтетическими данными
            data = {'timestamp': time_range}
            
            # Добавляем синтетические сигналы
            np.random.seed(42)  # Для воспроизводимости
            for i in range(5):  # 5 тестовых сигналов
                signal_name = f'TEST_SIGNAL_{i+1}'
                if i % 2 == 0:
                    # Булевые сигналы (0/1)
                    data[signal_name] = np.random.choice([0, 1], size=len(time_range))
                else:
                    # Аналоговые сигналы
                    data[signal_name] = np.random.normal(100, 20, size=len(time_range))
            
            df = pd.DataFrame(data)
            self.logger.info(f"Созданы синтетические данные: {len(df)} записей, {len(df.columns)-1} сигналов")
            return df
            
        except Exception as e:
            self.logger.error(f"Ошибка создания синтетических данных: {e}")
            import pandas as pd
            return pd.DataFrame()
