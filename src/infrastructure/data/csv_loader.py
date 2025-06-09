"""
Загрузчик CSV данных с исправлениями для сложной структуры файлов (ПОЛНАЯ ВЕРСИЯ)
"""
import pandas as pd
import logging
import chardet
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import re

from ...core.domain.entities.telemetry_data import TelemetryData


class CSVDataLoader:
    """ПОЛНЫЙ загрузчик CSV данных с обработкой сложной структуры"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Состояние для совместимости с legacy
        self.parameters = []
        self.lines = set()
        self.start_time = None
        self.end_time = None
        self.data = None

        self.logger.info("CSVDataLoader инициализирован")

    def _detect_encoding(self, file_path: str) -> str:
        """НОВОЕ: Автоопределение кодировки файла"""
        try:
            # Читаем первые 10KB для определения кодировки
            with open(file_path, 'rb') as f:
                raw_data = f.read(10240)

            # Используем chardet для определения кодировки
            detected = chardet.detect(raw_data)
            encoding = detected.get('encoding', 'utf-8')
            confidence = detected.get('confidence', 0)

            self.logger.info(
                f"Обнаружена кодировка: {encoding} (уверенность: {confidence:.2f})")

            # Приоритетный список кодировок для fallback
            fallback_encodings = [
                encoding,
                'cp1251',
                'windows-1251',
                'utf-8',
                'latin1',
                'cp1252'
            ]

            # Тестируем каждую кодировку
            for test_encoding in fallback_encodings:
                if test_encoding:
                    try:
                        with open(file_path, 'r', encoding=test_encoding) as f:
                            # Пытаемся прочитать первые 1000 символов
                            test_content = f.read(1000)

                        self.logger.info(
                            f"Успешно использована кодировка: {test_encoding}")
                        return test_encoding

                    except (UnicodeDecodeError, UnicodeError):
                        self.logger.debug(
                            f"Кодировка {test_encoding} не подошла")
                        continue

            # Последний резерв - ошибки игнорируем
            self.logger.warning(
                "Использована кодировка utf-8 с игнорированием ошибок")
            return 'utf-8'

        except Exception as e:
            self.logger.error(f"Ошибка определения кодировки: {e}")
            return 'utf-8'

    def _safe_file_read(self, file_path: str, encoding: str) -> list:
        """НОВОЕ: Безопасное чтение файла с обработкой ошибок кодировки"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.readlines()
        except UnicodeDecodeError as e:
            self.logger.warning(f"Ошибка кодировки {encoding}: {e}")

            # Пробуем с errors='replace'
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    lines = f.readlines()
                self.logger.info(
                    f"Файл прочитан с заменой проблемных символов")
                return lines
            except Exception as e2:
                self.logger.error(f"Критическая ошибка чтения файла: {e2}")
                raise

    def _safe_csv_read(self, file_path: str, encoding: str, **kwargs) -> pd.DataFrame:
        """НОВОЕ: Безопасное чтение CSV с обработкой ошибок кодировки"""
        try:
            return pd.read_csv(file_path, encoding=encoding, **kwargs)
        except UnicodeDecodeError as e:
            self.logger.warning(f"Ошибка кодировки CSV {encoding}: {e}")

            # Пробуем с errors='replace'
            try:
                return pd.read_csv(file_path, encoding=encoding, errors='replace', **kwargs)
            except Exception as e2:
                self.logger.error(f"Критическая ошибка чтения CSV: {e2}")
                raise

    def load_csv(self, file_path: str) -> TelemetryData:
        """ИСПРАВЛЕННАЯ загрузка CSV с обработкой сложной структуры"""
        try:
            self.logger.info(f"Загрузка CSV: {file_path}")

            # КРИТИЧНО: Определяем кодировку файла
            encoding = self._detect_encoding(file_path)

            # КРИТИЧНО: Предварительный анализ структуры файла
            header_row, metadata = self._analyze_csv_structure(
                file_path, encoding)

            if header_row is not None:
                # Загружаем с правильными заголовками и кодировкой
                df = self._safe_csv_read(
                    file_path,
                    encoding=encoding,
                    skiprows=header_row,
                    header=0,
                    sep=';',  # ВАЖНО: ваш файл использует ';'
                    low_memory=False
                )
            else:
                # Fallback к стандартной загрузке
                df = self._safe_csv_read(
                    file_path,
                    encoding=encoding,
                    sep=';',
                    low_memory=False
                )

            # КРИТИЧНО: Очистка и предобработка
            df = self._preprocess_csv_data(df)

            # КРИТИЧНО: Создание TelemetryData с правильными метаданными
            telemetry_data = self._create_telemetry_data(
                df, file_path, metadata)

            # Обновляем legacy атрибуты
            self._update_legacy_attributes(telemetry_data)

            self.logger.info(
                f"Загружено {len(df)} строк, {len(df.columns)} столбцов")

            return telemetry_data

        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV {file_path}: {e}")
            raise

    def _analyze_csv_structure(self, file_path: str, encoding: str) -> Tuple[Optional[int], Dict[str, str]]:
        """КРИТИЧНО: Анализ структуры CSV для поиска реальных заголовков"""
        metadata = {}
        header_row = None

        try:
            # ИСПРАВЛЕНО: Используем определенную кодировку
            lines = self._safe_file_read(file_path, encoding)

            for i, line in enumerate(lines):
                line = line.strip()

                # Извлекаем метаданные из начала файла
                if ':' in line and not '::' in line and i < 20:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().rstrip(';')
                        if key and value:
                            metadata[key] = value

                # КРИТИЧНО: Ищем строку с timestamp параметрами
                if ('TIMESTAMP_YEAR' in line and 'TIMESTAMP_MONTH' in line) or line.count('::') > 10:
                    header_row = i
                    self.logger.info(
                        f"Найдены реальные заголовки на строке {i}")
                    break

            # КРИТИЧНО: Обрабатываем специальные метаданные
            if 'Triggering date' in metadata and 'Triggering time' in metadata:
                trigger_date = metadata['Triggering date'].strip()
                trigger_time = metadata['Triggering time'].strip()
                metadata['real_timestamp'] = f"{trigger_date} {trigger_time}"
                self.logger.info(
                    f"Найдено реальное время: {metadata['real_timestamp']}")

            return header_row, metadata

        except Exception as e:
            self.logger.error(f"Ошибка анализа структуры CSV: {e}")
            return None, {}

    def _preprocess_csv_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """КРИТИЧНО: Предобработка данных"""
        try:
            # Удаляем полностью пустые строки и столбцы
            df = df.dropna(how='all').dropna(axis=1, how='all')

            # Очистка заголовков от лишних символов
            df.columns = [str(col).strip() for col in df.columns]

            # КРИТИЧНО: Удаляем строки с метаданными
            metadata_patterns = ['Date:', 'Case:',
                                 'Vehicle number:', 'Sampling period:']
            for pattern in metadata_patterns:
                if len(df) > 0 and len(df.columns) > 0:
                    mask = df.iloc[:, 0].astype(
                        str).str.contains(pattern, na=False)
                    df = df[~mask]

            # Конвертируем числовые столбцы
            for col in df.columns:
                if col != 'timestamp':
                    df[col] = pd.to_numeric(df[col], errors='ignore')

            self.logger.info(
                f"Предобработка завершена: {len(df)} строк, {len(df.columns)} столбцов")
            return df

        except Exception as e:
            self.logger.error(f"Ошибка предобработки данных: {e}")
            return df

    def _create_telemetry_data(self, df: pd.DataFrame, file_path: str, metadata: Dict[str, str]) -> TelemetryData:
        """КРИТИЧНО: Создание TelemetryData с правильными метаданными"""
        try:
            # КРИТИЧНО: Определяем временной диапазон из реальных данных
            if 'real_timestamp' in metadata:
                try:
                    base_time = pd.to_datetime(metadata['real_timestamp'])

                    # Получаем период дискретизации
                    sampling_period = 100  # По умолчанию 100ms
                    if 'Sampling period' in metadata:
                        try:
                            sampling_period = int(metadata['Sampling period'])
                        except:
                            pass

                    # Рассчитываем временной диапазон
                    duration_seconds = len(df) * sampling_period / 1000.0
                    start_time = base_time
                    end_time = base_time + timedelta(seconds=duration_seconds)

                    self.logger.info(
                        f"Использовано реальное время: {start_time} - {end_time}")

                except Exception as e:
                    self.logger.error(
                        f"Ошибка парсинга реального времени: {e}")
                    # Fallback
                    end_time = datetime.now()
                    start_time = end_time - timedelta(seconds=len(df))
            else:
                # Fallback к текущему времени
                end_time = datetime.now()
                start_time = end_time - timedelta(seconds=len(df))

            timestamp_range = (start_time, end_time)

            return TelemetryData(
                data=df,
                metadata=metadata,
                timestamp_range=timestamp_range,
                source_file=file_path
            )

        except Exception as e:
            self.logger.error(f"Ошибка создания TelemetryData: {e}")
            raise

    def _update_legacy_attributes(self, telemetry_data: TelemetryData):
        """Обновление атрибутов для совместимости с legacy кодом"""
        try:
            self.data = telemetry_data.data
            self.start_time = telemetry_data.timestamp_range[0]
            self.end_time = telemetry_data.timestamp_range[1]

            # Извлечение параметров
            self.parameters = self._extract_parameters(telemetry_data.data)
            self.lines = self._extract_lines(self.parameters)

            self.logger.debug(
                f"Legacy атрибуты обновлены: {len(self.parameters)} параметров")

        except Exception as e:
            self.logger.error(f"Ошибка обновления legacy атрибутов: {e}")

    def _extract_parameters(self, data: pd.DataFrame) -> list:
        """Извлечение параметров из данных"""
        parameters = []
        exclude_columns = {'timestamp', 'TIMESTAMP', 'index', 'time'}

        for column in data.columns:
            if column.lower() not in exclude_columns:
                param_info = self._parse_parameter_info(column)
                if param_info:
                    parameters.append(param_info)

        return parameters

    def _clean_description(self, description: str) -> str:
        """НОВЫЙ метод: Очистка описания от артефактов"""
        if not description:
            return ""

        # Удаляем артефакты "|0", "|", пустые значения
        artifacts = ['|0', '|', '0', 'nan', 'NaN', 'None', 'null']

        cleaned = description
        for artifact in artifacts:
            cleaned = cleaned.replace(artifact, '').strip()

        # Удаляем множественные пробелы
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    def _generate_description_from_code(self, signal_code: str) -> str:
        """НОВЫЙ метод: Генерация описания из кода сигнала"""
        try:
            parts = signal_code.split('_')
            if len(parts) > 1:
                # Убираем тип сигнала и номер вагона
                description_parts = []
                for part in parts[1:]:
                    if not part.isdigit():  # Пропускаем номера
                        description_parts.append(
                            part.replace('_', ' ').title())

                if description_parts:
                    return ' '.join(description_parts)

            # Fallback
            return signal_code.replace('_', ' ').title()

        except Exception:
            return signal_code

    def _parse_parameter_info(self, column_name: str) -> Optional[Dict[str, Any]]:
        """ИСПРАВЛЕННЫЙ парсинг с очисткой описания"""
        try:
            if '::' in column_name:
                signal_code, metadata = column_name.split('::', 1)

                if '|' in metadata:
                    line, description = metadata.split('|', 1)
                    line = line.strip()
                    description = description.strip()

                    # ИСПРАВЛЕНИЕ: Очищаем описание от артефактов
                    description = self._clean_description(description)

                    # Если описание пустое после очистки, генерируем новое
                    if not description:
                        description = self._generate_description_from_code(
                            signal_code)
                else:
                    line = metadata.strip()
                    description = self._generate_description_from_code(
                        signal_code)
            else:
                # Простой формат
                signal_code = column_name
                parts = column_name.split('_')
                signal_type = parts[0] if parts else 'Unknown'
                line = self._determine_line(signal_type)
                description = self._generate_description_from_code(signal_code)

            # ФИНАЛЬНАЯ очистка описания
            description = self._clean_description(description)

            return {
                'signal_code': signal_code.strip(),
                'full_column': column_name,
                'description': description,
                'line': line.strip(),
                'wagon': self._extract_wagon_number(signal_code),
                'signal_type': signal_code.split('_')[0] if '_' in signal_code else 'Unknown'
            }

        except Exception as e:
            self.logger.error(f"Ошибка парсинга параметра {column_name}: {e}")
            return None

    def _determine_line(self, signal_type: str) -> str:
        """Определение линии по типу сигнала"""
        line_mapping = {
            'B': 'L_CAN_BLOK_CH',
            'BY': 'L_CAN_ICU_CH_A',
            'W': 'L_TV_MAIN_CH_A',
            'DW': 'L_TV_MAIN_CH_B',
            'F': 'L_LCUP_CH_A',
            'WF': 'L_LCUP_CH_B'
        }
        return line_mapping.get(signal_type, 'UNKNOWN_LINE')

    def _extract_wagon_number(self, signal_code: str) -> str:
        """Извлечение номера вагона"""
        parts = signal_code.split('_')
        for part in reversed(parts):
            if part.isdigit():
                num = int(part)
                if 1 <= num <= 15:
                    return str(num)
        return '1'

    def _extract_lines(self, parameters: list) -> set:
        """Извлечение уникальных линий"""
        return {param['line'] for param in parameters if param.get('line')}

    def filter_changed_params(self, start_time, end_time) -> list:
        """Фильтрация изменяемых параметров для совместимости"""
        try:
            from datetime import datetime

            # Преобразование строк в datetime если необходимо
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

            self.logger.info(
                f"Фильтрация изменяемых параметров в диапазоне {start_time} - {end_time}")

            if not hasattr(self, 'data') or self.data is None:
                self.logger.warning("Нет данных для фильтрации")
                return []

            # Возвращаем все не системные параметры как потенциально изменяемые
            changed_params = []
            for param in self.parameters:
                try:
                    signal_code = param.get('signal_code', '').upper()
                    if 'TIMESTAMP' not in signal_code and not signal_code.startswith('DATE:'):
                        changed_params.append(param)
                except Exception:
                    changed_params.append(param)
                    continue

            self.logger.info(
                f"Найдено {len(changed_params)} потенциально изменяемых параметров")
            return changed_params

        except Exception as e:
            self.logger.error(f"Ошибка фильтрации изменяемых параметров: {e}")
            return []
