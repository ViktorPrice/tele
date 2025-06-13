"""
Загрузчик CSV данных с исправлениями для сложной структуры файлов и интеграцией с приоритетной логикой
"""
import pandas as pd
import logging
import chardet
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import re
import time
from pathlib import Path

# Импорт WagonConfig для карты вагонов
try:
    from ...infrastructure.sop.config.wagon_config import WagonConfig
except ImportError as e:
    logging.warning(f"WagonConfig недоступен: {e}")
    WagonConfig = None

# Импорты доменных сущностей
try:
    from ...core.domain.entities.telemetry_data import TelemetryData
    from ...core.domain.entities.parameter import Parameter
except ImportError as e:
    logging.warning(f"Доменные сущности недоступны: {e}")
    TelemetryData = None
    Parameter = None


class CSVDataLoader:
    """ПОЛНЫЙ загрузчик CSV данных с обработкой сложной структуры и приоритетной логикой"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Инициализация WagonConfig
        self.wagon_config = WagonConfig(self) if WagonConfig else None

        # Состояние для совместимости с legacy и main.py
        self.parameters = []
        self.lines = set()
        self.start_time = None
        self.end_time = None
        self.data = None
        
        # НОВЫЕ атрибуты для интеграции с исправленными компонентами
        self.min_timestamp = None
        self.max_timestamp = None
        self.records_count = 0
        
        # Кэш для производительности
        self._encoding_cache = {}
        self._structure_cache = {}
        
        # Статистика загрузки
        self._load_statistics = {}

        self.logger.info("CSVDataLoader инициализирован с приоритетной поддержкой")

    def get_parameters(self) -> list:
        """Возвращает текущий список параметров"""
        self.logger.debug(f"get_parameters вызван, возвращается {len(self.parameters)} параметров")
        return self.parameters

    def get_controlling_wagon(self) -> int:
        """ИСПРАВЛЕННОЕ извлечение сквозного номера ведущего вагона из данных и обновление карты вагонов"""
        try:
            # КРИТИЧЕСКАЯ ПРОВЕРКА: наличие данных
            if self.data is None:
                self.logger.debug("Данные не загружены, используется вагон по умолчанию")
                return 1

            # КРИТИЧЕСКАЯ ПРОВЕРКА: наличие столбца
            if 'DW_CURRENT_ID_WAGON' not in self.data.columns:
                self.logger.debug("Столбец DW_CURRENT_ID_WAGON не найден, ищем альтернативные столбцы")
                
                # Поиск альтернативных столбцов для определения ведущего вагона
                alternative_columns = [
                    'CURRENT_ID_WAGON',
                    'ID_WAGON',
                    'WAGON_ID',
                    'CONTROLLING_WAGON',
                    'LEAD_WAGON'
                ]
                
                found_column = None
                for alt_col in alternative_columns:
                    if alt_col in self.data.columns:
                        found_column = alt_col
                        self.logger.info(f"Найден альтернативный столбец для ведущего вагона: {alt_col}")
                        break
                
                if not found_column:
                    # Пытаемся найти столбец по паттерну
                    wagon_columns = [col for col in self.data.columns if 'WAGON' in col.upper()]
                    if wagon_columns:
                        found_column = wagon_columns[0]
                        self.logger.info(f"Найден столбец по паттерну WAGON: {found_column}")
                    else:
                        self.logger.info("Столбцы с информацией о вагоне не найдены, используется вагон по умолчанию")
                        return 1
                
                # Используем найденный альтернативный столбец
                column_to_use = found_column
            else:
                column_to_use = 'DW_CURRENT_ID_WAGON'

            # БЕЗОПАСНОЕ извлечение значения
            wagon_series = self.data[column_to_use].dropna()
            
            if len(wagon_series) == 0:
                self.logger.info(f"Столбец {column_to_use} не содержит данных, используется вагон по умолчанию")
                return 1

            # Берем последнее значение столбца
            last_value = wagon_series.iloc[-1]

            # УЛУЧШЕННАЯ обработка номера вагона
            wagon_num = self._extract_wagon_number_from_value(last_value)
            
            if wagon_num is None:
                self.logger.warning(f"Не удалось извлечь номер вагона из значения: {last_value}")
                return 1

            # Валидация номера вагона
            if not (1 <= wagon_num <= 16):
                self.logger.warning(f"Номер вагона {wagon_num} вне допустимого диапазона [1-16], используется 1")
                wagon_num = 1

            # Обновляем карту вагонов в зависимости от номера
            if self.wagon_config:
                self._update_wagon_map_based_on_controlling_wagon(wagon_num)

            self.logger.info(f"Определен ведущий вагон: {wagon_num}")
            return wagon_num

        except Exception as e:
            self.logger.error(f"Ошибка в get_controlling_wagon: {e}")
            return 1

    def _extract_wagon_number_from_value(self, value) -> Optional[int]:
        """НОВЫЙ МЕТОД: Извлечение номера вагона из значения с различными форматами"""
        try:
            # Преобразуем в строку
            value_str = str(value).strip()
            
            # Если это уже число в допустимом диапазоне
            try:
                direct_num = int(float(value_str))
                if 1 <= direct_num <= 16:
                    return direct_num
            except (ValueError, OverflowError):
                pass
            
            # Если это длинное число, берем последние 2 цифры
            if len(value_str) >= 2 and value_str.isdigit():
                last_two_digits = value_str[-2:]
                try:
                    wagon_num = int(last_two_digits)
                    if 1 <= wagon_num <= 16:
                        return wagon_num
                except ValueError:
                    pass
            
            # Поиск числа в строке с помощью регулярных выражений
            number_matches = re.findall(r'\d+', value_str)
            for match in reversed(number_matches):  # Начинаем с последнего найденного числа
                try:
                    num = int(match)
                    if 1 <= num <= 16:
                        return num
                    # Если число больше 16, берем последние цифры
                    if num > 16:
                        last_digits = int(str(num)[-2:]) if len(str(num)) >= 2 else int(str(num)[-1:])
                        if 1 <= last_digits <= 16:
                            return last_digits
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения номера вагона из значения {value}: {e}")
            return None

    def _update_wagon_map_based_on_controlling_wagon(self, wagon_num: int):
        """НОВЫЙ МЕТОД: Обновление карты вагонов на основе ведущего вагона"""
        try:
            if wagon_num == 1:
                new_map = {
                    1: "1г", 2: "11бо", 3: "2м", 4: "3нм", 5: "6м",
                    6: "8м", 7: "7нм", 8: "12м", 9: "13бо", 10: "10м", 11: "9г"
                }
                self.logger.info("Применена карта вагонов для ведущего вагона 1")
            elif wagon_num == 9:
                new_map = {
                    11: "1г", 10: "11бо", 9: "2м", 8: "3нм", 7: "6м",
                    6: "8м", 5: "7нм", 4: "12м", 3: "13бо", 2: "10м", 1: "9г"
                }
                self.logger.info("Применена карта вагонов для ведущего вагона 9")
            else:
                # Для других вагонов используем карту по умолчанию
                new_map = self.wagon_config.get_wagon_number_map()
                self.logger.info(f"Применена карта вагонов по умолчанию для ведущего вагона {wagon_num}")

            self.wagon_config.update_wagon_map(new_map)
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления карты вагонов: {e}")

    def extract_and_update_mcd_info(self, file_path: str):
        """Извлечение и обновление информации о МЦД из данных CSV файла"""
        try:
            if not file_path:
                return None
                
            # Проверяем, что данные загружены
            if self.data is None or self.data.empty:
                self.logger.warning("Данные не загружены, невозможно извлечь информацию о МЦД")
                return None
            
            mcd_info = {
                'line_mcd': '',
                'route': '',
                'train': '',
                'leading_unit': ''
            }
            
            # Извлекаем информацию из DW_CURRENT_ID_WAGON
            wagon_col = None
            for col in self.data.columns:
                if col.startswith('DW_CURRENT_ID_WAGON'):
                    wagon_col = col
                    self.logger.info(f"Найден столбец для ведущего вагона: {col}")
                    break
            
            if wagon_col:
                wagon_series = self.data[wagon_col].dropna()
                
                if len(wagon_series) > 0:
                    # Берем последнее значение
                    wagon_value = str(wagon_series.iloc[-1]).strip()
                    
                    if len(wagon_value) >= 5:  # Минимум 5 цифр (4 цифры типа + 3 цифры состава + 2 цифры вагона)
                        try:
                            # Последние 2 цифры - номер ведущего вагона
                            leading_unit = wagon_value[-2:]
                            mcd_info['leading_unit'] = leading_unit
                            
                            # 3 цифры перед номером вагона - номер состава
                            if len(wagon_value) >= 5:
                                train_num = wagon_value[-5:-2]
                                mcd_info['train'] = train_num
                                
                            self.logger.info(f"Извлечено из {wagon_col}: состав={train_num}, ведущий вагон={leading_unit}")
                            
                        except Exception as e:
                            self.logger.error(f"Ошибка парсинга {wagon_col}: {e}")
                else:
                    self.logger.warning(f"Столбец {wagon_col} пуст, невозможно извлечь информацию о МЦД")
                    self.logger.warning("Не удалось извлечь информацию о МЦД ни из данных, ни из имени файла")
                    return None
            else:
                self.logger.warning("Столбец DW_CURRENT_ID_WAGON отсутствует, невозможно извлечь информацию о МЦД")
                self.logger.warning("Не удалось извлечь информацию о МЦД ни из данных, ни из имени файла")
                return None
            
            # Извлекаем информацию из W_BUIK_TRAIN_NUM
            train_col = None
            for col in self.data.columns:
                if col.startswith('W_BUIK_TRAIN_NUM'):
                    train_col = col
                    self.logger.info(f"Найден столбец для номера маршрута: {col}")
                    break
            
            if train_col:
                train_num_series = self.data[train_col].dropna()
                
                if len(train_num_series) > 0:
                    # Берем последнее значение
                    train_num_value = str(train_num_series.iloc[-1]).strip()
                    
                    if len(train_num_value) >= 5:  # Минимум 5 цифр (1 цифра линии + 4 цифры маршрута)
                        try:
                            # Первая цифра - номер линии МЦД
                            line_mcd = train_num_value[0]
                            mcd_info['line_mcd'] = line_mcd
                            
                            # Четыре последующие цифры - номер маршрута
                            route = train_num_value[1:5]
                            mcd_info['route'] = route
                            
                            self.logger.info(f"Извлечено из {train_col}: линия МЦД={line_mcd}, маршрут={route}")
                            
                        except Exception as e:
                            self.logger.error(f"Ошибка парсинга {train_col}: {e}")
                else:
                    self.logger.warning(f"Столбец {train_col} пуст, невозможно извлечь информацию о МЦД")
                    self.logger.warning("Не удалось извлечь информацию о МЦД ни из данных, ни из имени файла")
                    return None
            else:
                self.logger.warning("Столбец W_BUIK_TRAIN_NUM отсутствует, невозможно извлечь информацию о МЦД")
                self.logger.warning("Не удалось извлечь информацию о МЦД ни из данных, ни из имени файла")
                return None
            
            # Проверяем, что хотя бы что-то извлечено
            if any(mcd_info.values()):
                self.logger.info(f"Успешно извлечена информация МЦД: {mcd_info}")
                return mcd_info
            else:
                self.logger.warning("Не удалось извлечь информацию о МЦД ни из данных, ни из имени файла")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка извлечения информации о МЦД: {e}")
            return None

    def _extract_mcd_from_alternative_columns(self) -> Dict[str, str]:
        """Поиск информации о МЦД в альтернативных столбцах"""
        mcd_info = {
            'line_mcd': '',
            'route': '',
            'train': '',
            'leading_unit': ''
        }
        
        try:
            # Альтернативные названия столбцов для поиска
            wagon_alternatives = [
                'CURRENT_ID_WAGON', 'ID_WAGON', 'WAGON_ID', 
                'CONTROLLING_WAGON', 'LEAD_WAGON'
            ]
            
            train_alternatives = [
                'TRAIN_NUM', 'BUIK_TRAIN_NUM', 'TRAIN_NUMBER',
                'ROUTE_NUM', 'ROUTE_NUMBER'
            ]
            
            # Поиск альтернативных столбцов для вагона
            for alt_col in wagon_alternatives:
                if alt_col in self.data.columns:
                    series = self.data[alt_col].dropna()
                    if len(series) > 0:
                        value = str(series.iloc[-1]).strip()
                        if len(value) >= 2:
                            mcd_info['leading_unit'] = value[-2:]
                            if len(value) >= 5:
                                mcd_info['train'] = value[-5:-2]
                            break
            
            # Поиск альтернативных столбцов для маршрута
            for alt_col in train_alternatives:
                if alt_col in self.data.columns:
                    series = self.data[alt_col].dropna()
                    if len(series) > 0:
                        value = str(series.iloc[-1]).strip()
                        if len(value) >= 5:
                            mcd_info['line_mcd'] = value[0]
                            mcd_info['route'] = value[1:5]
                            break
            
            return mcd_info
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска в альтернативных столбцах: {e}")
            return mcd_info

    def _extract_mcd_from_filename(self, file_path: str) -> Dict[str, str]:
        """Fallback: извлечение информации о МЦД из имени файла"""
        mcd_info = {
            'line_mcd': '',
            'route': '',
            'train': '',
            'leading_unit': ''
        }
        
        try:
            from pathlib import Path
            import re
            
            file_name = Path(file_path).stem
            
            # МЦД линия
            mcd_match = re.search(r'MCD[_-]?(\d+)', file_name, re.IGNORECASE)
            if mcd_match:
                mcd_info['line_mcd'] = mcd_match.group(1)
            
            # Маршрут
            route_match = re.search(r'Route[_-]?(\w+)', file_name, re.IGNORECASE)
            if route_match:
                mcd_info['route'] = route_match.group(1)
            elif re.search(r'(\d{3,4})', file_name):
                route_num = re.search(r'(\d{3,4})', file_name)
                mcd_info['route'] = route_num.group(1)
            
            # Состав
            train_match = re.search(r'Train[_-]?(\w+)', file_name, re.IGNORECASE)
            if train_match:
                mcd_info['train'] = train_match.group(1)
            elif re.search(r'(\d{4,5})', file_name):
                train_num = re.search(r'(\d{4,5})', file_name)
                mcd_info['train'] = train_num.group(1)
            
            # Ведущая голова
            unit_match = re.search(r'Unit[_-]?(\w+)', file_name, re.IGNORECASE)
            if unit_match:
                mcd_info['leading_unit'] = unit_match.group(1)
            elif re.search(r'Head[_-]?(\w+)', file_name, re.IGNORECASE):
                head_match = re.search(r'Head[_-]?(\w+)', file_name, re.IGNORECASE)
                mcd_info['leading_unit'] = head_match.group(1)
            
            return mcd_info
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения из имени файла: {e}")
            return mcd_info

    def get_mcd_info_summary(self) -> Dict[str, Any]:
        """Получение сводной информации о МЦД для отчетов"""
        try:
            summary = {
                'has_mcd_data': False,
                'line_mcd': None,
                'route': None,
                'train_number': None,
                'leading_wagon': None,
                'data_sources': []
            }
            
            # Проверяем наличие ключевых столбцов
            if self.data is not None:
                if 'DW_CURRENT_ID_WAGON' in self.data.columns:
                    summary['data_sources'].append('DW_CURRENT_ID_WAGON')
                    summary['has_mcd_data'] = True
                    
                if 'W_BUIK_TRAIN_NUM' in self.data.columns:
                    summary['data_sources'].append('W_BUIK_TRAIN_NUM')
                    summary['has_mcd_data'] = True
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Ошибка получения сводки МЦД: {e}")
            return {'has_mcd_data': False, 'error': str(e)}    

    def _detect_encoding(self, file_path: str) -> str:
        """УЛУЧШЕННОЕ автоопределение кодировки файла с кэшированием"""
        try:
            # Проверяем кэш
            if file_path in self._encoding_cache:
                return self._encoding_cache[file_path]

            # Читаем первые 10KB для определения кодировки
            with open(file_path, 'rb') as f:
                raw_data = f.read(10240)

            # Используем chardet для определения кодировки
            detected = chardet.detect(raw_data)
            encoding = detected.get('encoding', 'utf-8')
            confidence = detected.get('confidence', 0)

            self.logger.info(f"Обнаружена кодировка: {encoding} (уверенность: {confidence:.2f})")

            # РАСШИРЕННЫЙ приоритетный список кодировок для fallback
            fallback_encodings = [
                encoding,
                'cp1251',
                'windows-1251',
                'utf-8',
                'utf-8-sig',  # UTF-8 с BOM
                'latin1',
                'cp1252',
                'iso-8859-1'
            ]

            # Тестируем каждую кодировку
            for test_encoding in fallback_encodings:
                if test_encoding:
                    try:
                        with open(file_path, 'r', encoding=test_encoding) as f:
                            # Пытаемся прочитать первые 1000 символов
                            test_content = f.read(1000)
                            
                        self.logger.info(f"Успешно использована кодировка: {test_encoding}")
                        
                        # Кэшируем результат
                        self._encoding_cache[file_path] = test_encoding
                        return test_encoding

                    except (UnicodeDecodeError, UnicodeError):
                        self.logger.debug(f"Кодировка {test_encoding} не подошла")
                        continue

            # Последний резерв - ошибки игнорируем
            self.logger.warning("Использована кодировка utf-8 с игнорированием ошибок")
            fallback_encoding = 'utf-8'
            self._encoding_cache[file_path] = fallback_encoding
            return fallback_encoding

        except Exception as e:
            self.logger.error(f"Ошибка определения кодировки: {e}")
            return 'utf-8'

    def _safe_file_read(self, file_path: str, encoding: str) -> List[str]:
        """УЛУЧШЕННОЕ безопасное чтение файла с обработкой ошибок кодировки"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.readlines()
        except UnicodeDecodeError as e:
            self.logger.warning(f"Ошибка кодировки {encoding}: {e}")

            # Пробуем с errors='replace'
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    lines = f.readlines()
                self.logger.info("Файл прочитан с заменой проблемных символов")
                return lines
            except Exception as e2:
                self.logger.error(f"Критическая ошибка чтения файла: {e2}")
                raise

    def _safe_csv_read(self, file_path: str, encoding: str, **kwargs) -> pd.DataFrame:
        """УЛУЧШЕННОЕ безопасное чтение CSV с обработкой ошибок кодировки"""
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

    def load_csv(self, file_path: str) -> Optional[TelemetryData]:
        """ПРИОРИТЕТНАЯ загрузка CSV с интеграцией в исправленную архитектуру"""
        start_time = time.time()
        
        try:
            self.logger.info(f"ПРИОРИТЕТНАЯ загрузка CSV: {file_path}")

            # Очищаем предыдущие данные
            self._clear_previous_data()

            # КРИТИЧНО: Определяем кодировку файла
            encoding = self._detect_encoding(file_path)

            # КРИТИЧНО: Предварительный анализ структуры файла
            header_row, metadata = self._analyze_csv_structure_enhanced(file_path, encoding)

            # Загружаем данные с правильными параметрами
            df = self._load_csv_data_enhanced(file_path, encoding, header_row)

            if df is None or df.empty:
                self.logger.error("Не удалось загрузить данные или файл пуст")
                return None

            # КРИТИЧНО: Очистка и предобработка
            df = self._preprocess_csv_data_enhanced(df)

            # КРИТИЧНО: Создание TelemetryData с правильными метаданными
            telemetry_data = self._create_telemetry_data_enhanced(df, file_path, metadata)

            # ПРИОРИТЕТНОЕ обновление атрибутов для интеграции
            self._update_integration_attributes(telemetry_data)

            # Сбор статистики
            load_time = time.time() - start_time
            self._collect_load_statistics_enhanced(file_path, load_time, df, metadata)

            self.logger.info(f"ПРИОРИТЕТНАЯ загрузка завершена за {load_time:.2f}с: {len(df)} строк, {len(df.columns)} столбцов")

            return telemetry_data

        except Exception as e:
            load_time = time.time() - start_time
            self.logger.error(f"Ошибка приоритетной загрузки CSV {file_path}: {e} (время: {load_time:.2f}с)")
            return None

    def _clear_previous_data(self):
        """Очистка предыдущих данных"""
        self.parameters = []
        self.lines = set()
        self.start_time = None
        self.end_time = None
        self.data = None
        self.min_timestamp = None
        self.max_timestamp = None
        self.records_count = 0

    def _analyze_csv_structure_enhanced(self, file_path: str, encoding: str) -> Tuple[Optional[int], Dict[str, str]]:
        """РАСШИРЕННЫЙ анализ структуры CSV для поиска реальных заголовков"""
        metadata = {}
        header_row = None

        try:
            # Проверяем кэш структуры
            cache_key = f"{file_path}_{encoding}"
            if cache_key in self._structure_cache:
                return self._structure_cache[cache_key]

            # Используем определенную кодировку
            lines = self._safe_file_read(file_path, encoding)

            for i, line in enumerate(lines):
                line = line.strip()

                # Извлекаем метаданные из начала файла
                if ':' in line and not '::' in line and i < 30:  # Увеличили лимит поиска
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().rstrip(';')
                        if key and value:
                            metadata[key] = value

                # КРИТИЧНО: Расширенный поиск строки с заголовками
                header_indicators = [
                    'TIMESTAMP_YEAR',
                    'TIMESTAMP_MONTH', 
                    'TIMESTAMP_DAY',
                    'TIMESTAMP_HOUR',
                    'TIMESTAMP_MINUTE',
                    'TIMESTAMP_SECOND'
                ]
                
                if any(indicator in line for indicator in header_indicators) or line.count('::') > 10:
                    header_row = i
                    self.logger.info(f"Найдены реальные заголовки на строке {i}")
                    break

                # Дополнительная проверка на строки с большим количеством разделителей
                if line.count(';') > 20 and i < 50:  # Много столбцов
                    if not any(char.isalpha() for char in line.split(';')[0]):  # Первый столбец не содержит букв
                        continue  # Это данные, не заголовки
                    header_row = i
                    self.logger.info(f"Найдены заголовки по количеству разделителей на строке {i}")
                    break

            # КРИТИЧНО: Обрабатываем специальные метаданные
            self._process_metadata_enhanced(metadata)

            # Кэшируем результат
            result = (header_row, metadata)
            self._structure_cache[cache_key] = result
            
            return result

        except Exception as e:
            self.logger.error(f"Ошибка анализа структуры CSV: {e}")
            return None, {}

    def _process_metadata_enhanced(self, metadata: Dict[str, str]):
        """РАСШИРЕННАЯ обработка метаданных"""
        try:
            # Обработка времени запуска
            if 'Triggering date' in metadata and 'Triggering time' in metadata:
                trigger_date = metadata['Triggering date'].strip()
                trigger_time = metadata['Triggering time'].strip()
                metadata['real_timestamp'] = f"{trigger_date} {trigger_time}"
                self.logger.info(f"Найдено реальное время: {metadata['real_timestamp']}")

            # Обработка периода дискретизации
            if 'Sampling period' in metadata:
                try:
                    sampling_str = metadata['Sampling period'].strip()
                    # Извлекаем числовое значение
                    sampling_match = re.search(r'(\d+)', sampling_str)
                    if sampling_match:
                        metadata['sampling_period_ms'] = int(sampling_match.group(1))
                        self.logger.info(f"Период дискретизации: {metadata['sampling_period_ms']} мс")
                except Exception as e:
                    self.logger.warning(f"Ошибка обработки периода дискретизации: {e}")

            # Обработка информации о поезде
            if 'Vehicle number' in metadata:
                metadata['vehicle_number'] = metadata['Vehicle number'].strip()

            # Обработка номера случая
            if 'Case' in metadata:
                metadata['case_number'] = metadata['Case'].strip()

        except Exception as e:
            self.logger.error(f"Ошибка обработки метаданных: {e}")

    def _load_csv_data_enhanced(self, file_path: str, encoding: str, header_row: Optional[int]) -> Optional[pd.DataFrame]:
        """РАСШИРЕННАЯ загрузка CSV данных"""
        try:
            read_params = {
                'encoding': encoding,
                'sep': ';',  # ВАЖНО: файлы используют ';'
                'low_memory': False,
                'na_values': ['', 'nan', 'NaN', 'NULL', 'null'],
                'keep_default_na': True
            }

            if header_row is not None:
                read_params.update({
                    'skiprows': header_row,
                    'header': 0
                })
                self.logger.info(f"Загрузка с заголовками на строке {header_row}")
            else:
                self.logger.info("Загрузка без пропуска строк")

            df = self._safe_csv_read(file_path, **read_params)

            if df.empty:
                self.logger.error("Загруженный DataFrame пуст")
                return None

            self.logger.info(f"Первичная загрузка: {len(df)} строк, {len(df.columns)} столбцов")
            return df

        except Exception as e:
            self.logger.error(f"Ошибка загрузки CSV данных: {e}")
            return None

    def _preprocess_csv_data_enhanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """РАСШИРЕННАЯ предобработка данных"""
        try:
            original_shape = df.shape
            
            # Удаляем полностью пустые строки и столбцы
            df = df.dropna(how='all').dropna(axis=1, how='all')

            # Очистка заголовков от лишних символов
            df.columns = [str(col).strip() for col in df.columns]

            # КРИТИЧНО: Удаляем строки с метаданными в данных
            metadata_patterns = [
                'Date:', 'Case:', 'Vehicle number:', 'Sampling period:',
                'Triggering date:', 'Triggering time:', 'Comment:'
            ]
            
            for pattern in metadata_patterns:
                if len(df) > 0 and len(df.columns) > 0:
                    # Проверяем первый столбец
                    mask = df.iloc[:, 0].astype(str).str.contains(pattern, na=False, case=False)
                    df = df[~mask]

            # Удаляем строки где первый столбец содержит только текст (не числа)
            if len(df) > 0 and len(df.columns) > 0:
                first_col = df.iloc[:, 0]
                # Оставляем только строки где первый столбец может быть преобразован в число
                numeric_mask = pd.to_numeric(first_col, errors='coerce').notna()
                df = df[numeric_mask]

            # ПРИОРИТЕТНАЯ конвертация числовых столбцов
            for col in df.columns:
                if col.upper() not in ['TIMESTAMP', 'TIME', 'INDEX']:
                    # Пытаемся конвертировать в числовой тип с обработкой исключений
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except Exception as e:
                        self.logger.warning(f"Не удалось конвертировать столбец {col} в числовой тип: {e}")

            # Сброс индекса после фильтрации
            df = df.reset_index(drop=True)

            self.logger.info(f"Предобработка завершена: {original_shape} -> {df.shape}")
            return df

        except Exception as e:
            self.logger.error(f"Ошибка предобработки данных: {e}")
            return df

    def _create_telemetry_data_enhanced(self, df: pd.DataFrame, file_path: str, metadata: Dict[str, str]) -> TelemetryData:
        """ИСПРАВЛЕНО: Создание TelemetryData без присвоения records_count"""
        try:
            # КРИТИЧНО: Определяем временной диапазон из реальных данных
            timestamp_range = self._calculate_timestamp_range_enhanced(df, metadata)

            # Создаем TelemetryData если класс доступен
            if TelemetryData:
                telemetry_data = TelemetryData(
                    data=df,
                    metadata=metadata,
                    timestamp_range=timestamp_range,
                    source_file=file_path
                )
                
                # ИСПРАВЛЕНО: Убираем присвоение records_count (это property без сеттера)
                # telemetry_data.records_count = len(df)  # УДАЛЕНО
                telemetry_data.columns_count = len(df.columns)
                
                return telemetry_data
            else:
                # Fallback объект если TelemetryData недоступен
                class FallbackTelemetryData:
                    def __init__(self, data, metadata, timestamp_range, source_file):
                        self.data = data
                        self.metadata = metadata
                        self.timestamp_range = timestamp_range
                        self.source_file = source_file
                        self.records_count = len(data)
                        self.columns_count = len(data.columns)

                return FallbackTelemetryData(df, metadata, timestamp_range, file_path)

        except Exception as e:
            self.logger.error(f"Ошибка создания TelemetryData: {e}")
            raise

    def _calculate_timestamp_range_enhanced(self, df: pd.DataFrame, metadata: Dict[str, str]) -> Tuple[datetime, datetime]:
        """РАСШИРЕННЫЙ расчет временного диапазона"""
        try:
            # Способ 1: Из метаданных с реальным временем
            if 'real_timestamp' in metadata:
                try:
                    base_time = pd.to_datetime(metadata['real_timestamp'])
                    
                    # Получаем период дискретизации
                    sampling_period = metadata.get('sampling_period_ms', 100)  # По умолчанию 100ms
                    
                    # Рассчитываем временной диапазон
                    duration_seconds = len(df) * sampling_period / 1000.0
                    start_time = base_time
                    end_time = base_time + timedelta(seconds=duration_seconds)

                    self.logger.info(f"Использовано реальное время: {start_time} - {end_time}")
                    return (start_time, end_time)

                except Exception as e:
                    self.logger.error(f"Ошибка парсинга реального времени: {e}")

            # Способ 2: Из timestamp столбцов если есть
            timestamp_columns = [col for col in df.columns if 'TIMESTAMP' in col.upper()]
            if timestamp_columns:
                try:
                    # Пытаемся построить timestamp из компонентов
                    timestamp_range = self._build_timestamp_from_components(df, timestamp_columns)
                    if timestamp_range:
                        return timestamp_range
                except Exception as e:
                    self.logger.warning(f"Ошибка построения timestamp из компонентов: {e}")

            # Способ 3: Fallback к текущему времени
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=len(df))
            
            self.logger.warning(f"Использовано fallback время: {start_time} - {end_time}")
            return (start_time, end_time)

        except Exception as e:
            self.logger.error(f"Ошибка расчета временного диапазона: {e}")
            # Критический fallback
            now = datetime.now()
            return (now - timedelta(hours=1), now)

    def _build_timestamp_from_components(self, df: pd.DataFrame, timestamp_columns: List[str]) -> Optional[Tuple[datetime, datetime]]:
        """Построение timestamp из компонентов"""
        try:
            # Ищем компоненты времени
            components = {}
            for col in timestamp_columns:
                col_upper = col.upper()
                if 'YEAR' in col_upper:
                    components['year'] = col
                elif 'MONTH' in col_upper:
                    components['month'] = col
                elif 'DAY' in col_upper:
                    components['day'] = col
                elif 'HOUR' in col_upper:
                    components['hour'] = col
                elif 'MINUTE' in col_upper:
                    components['minute'] = col
                elif 'SECOND' in col_upper:
                    components['second'] = col

            # Проверяем наличие основных компонентов
            required = ['year', 'month', 'day', 'hour', 'minute', 'second']
            if not all(comp in components for comp in required):
                self.logger.warning("Не все компоненты времени найдены")
                return None

            # Берем первую и последнюю строки для диапазона
            first_row = df.iloc[0]
            last_row = df.iloc[-1]

            start_time = datetime(
                year=int(first_row[components['year']]),
                month=int(first_row[components['month']]),
                day=int(first_row[components['day']]),
                hour=int(first_row[components['hour']]),
                minute=int(first_row[components['minute']]),
                second=int(first_row[components['second']])
            )

            end_time = datetime(
                year=int(last_row[components['year']]),
                month=int(last_row[components['month']]),
                day=int(last_row[components['day']]),
                hour=int(last_row[components['hour']]),
                minute=int(last_row[components['minute']]),
                second=int(last_row[components['second']])
            )

            self.logger.info(f"Построен timestamp из компонентов: {start_time} - {end_time}")
            return (start_time, end_time)

        except Exception as e:
            self.logger.error(f"Ошибка построения timestamp из компонентов: {e}")
            return None

    def _update_integration_attributes(self, telemetry_data):
        """ПРИОРИТЕТНОЕ обновление атрибутов для интеграции с исправленными компонентами"""
        try:
            # Основные атрибуты для совместимости
            self.data = telemetry_data.data
            self.records_count = telemetry_data.records_count

            # ПРИОРИТЕТНЫЕ атрибуты для временного диапазона
            if telemetry_data.timestamp_range:
                self.start_time = telemetry_data.timestamp_range[0]
                self.end_time = telemetry_data.timestamp_range[1]
                
                # КРИТИЧНО: Форматируем для интеграции с main_controller.py
                self.min_timestamp = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
                self.max_timestamp = self.end_time.strftime('%Y-%m-%d %H:%M:%S')

            # ПРИОРИТЕТНОЕ извлечение параметров для изменяемых параметров
            self.parameters = self._extract_parameters_enhanced(telemetry_data.data)
            self.lines = self._extract_lines_enhanced(self.parameters)

            self.logger.info(f"Атрибуты интеграции обновлены: {len(self.parameters)} параметров, {len(self.lines)} линий")

        except Exception as e:
            self.logger.error(f"Ошибка обновления атрибутов интеграции: {e}")

    def _extract_parameters_enhanced(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """РАСШИРЕННОЕ извлечение параметров из данных"""
        parameters = []
        exclude_columns = {'timestamp', 'TIMESTAMP', 'index', 'time', 'TIME'}

        try:
            for column in data.columns:
                if column.lower() not in {col.lower() for col in exclude_columns}:
                    param_info = self._parse_parameter_info_enhanced(column)
                    if param_info:
                        # Используем WagonConfig для преобразования номера вагона
                        if self.wagon_config:
                            try:
                                skvoz_num = int(param_info.get('wagon', '1'))
                                real_wagon = self.wagon_config.get_real_wagon_number(skvoz_num)
                                param_info['wagon'] = real_wagon
                            except Exception as e:
                                self.logger.warning(f"Ошибка преобразования номера вагона: {e}")

                        # ПРИОРИТЕТНАЯ проверка на изменяемость
                        param_info['is_potentially_changed'] = self._is_potentially_changed_parameter(data[column])
                        parameters.append(param_info)

            self.logger.info(f"Извлечено {len(parameters)} параметров")
            return parameters

        except Exception as e:
            self.logger.error(f"Ошибка извлечения параметров: {e}")
            return []

    def _is_potentially_changed_parameter(self, series: pd.Series) -> bool:
        """НОВЫЙ МЕТОД: Быстрая проверка потенциальной изменяемости параметра"""
        try:
            clean_series = series.dropna()
            
            if len(clean_series) < 2:
                return False
            
            # Быстрая проверка уникальности
            unique_count = len(clean_series.unique())
            total_count = len(clean_series)
            
            # Если все значения одинаковые - не изменяемый
            if unique_count == 1:
                return False
            
            # Если слишком много уникальных значений - возможно изменяемый
            if unique_count > total_count * 0.1:
                return True
            
            # Для числовых данных проверяем диапазон
            if clean_series.dtype.kind in 'biufc':
                value_range = clean_series.max() - clean_series.min()
                return value_range > 0
            
            return unique_count > 1

        except Exception:
            return False

    def _parse_parameter_info_enhanced(self, column_name: str) -> Optional[Dict[str, Any]]:
        """РАСШИРЕННЫЙ парсинг параметров с улучшенной очисткой"""
        try:
            if '::' in column_name:
                signal_code, metadata = column_name.split('::', 1)

                if '|' in metadata:
                    line, description = metadata.split('|', 1)
                    line = line.strip()
                    description = description.strip()

                    # РАСШИРЕННАЯ очистка описания
                    description = self._clean_description_enhanced(description)

                    # Если описание пустое после очистки, генерируем новое
                    if not description:
                        description = self._generate_description_from_code_enhanced(signal_code)
                else:
                    line = metadata.strip()
                    description = self._generate_description_from_code_enhanced(signal_code)
            else:
                # Простой формат
                signal_code = column_name
                parts = column_name.split('_')
                signal_type = parts[0] if parts else 'Unknown'
                line = self._determine_line_enhanced(signal_type)
                description = self._generate_description_from_code_enhanced(signal_code)

            # ФИНАЛЬНАЯ очистка описания
            description = self._clean_description_enhanced(description)

            # РАСШИРЕННАЯ информация о параметре
            param_info = {
                'signal_code': signal_code.strip(),
                'full_column': column_name,
                'description': description,
                'line': line.strip(),
                'wagon': self._extract_wagon_number_enhanced(signal_code),
                'signal_type': signal_code.split('_')[0] if '_' in signal_code else 'Unknown',
                'data_type': self._determine_data_type(signal_code),
                'is_problematic': self._is_problematic_parameter(signal_code, description),
                'plot': False  # По умолчанию не выбран для графика
            }

            return param_info

        except Exception as e:
            self.logger.error(f"Ошибка парсинга параметра {column_name}: {e}")
            return None

    def _clean_description_enhanced(self, description: str) -> str:
        """РАСШИРЕННАЯ очистка описания от артефактов"""
        if not description:
            return ""

        # Расширенный список артефактов
        artifacts = ['|0', '|', '0', 'nan', 'NaN', 'None', 'null', 'NULL', '""', "''"]

        cleaned = description
        for artifact in artifacts:
            cleaned = cleaned.replace(artifact, '').strip()

        # Удаляем множественные пробелы и специальные символы
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', cleaned).strip()

        return cleaned

    def _generate_description_from_code_enhanced(self, signal_code: str) -> str:
        """РАСШИРЕННАЯ генерация описания из кода сигнала"""
        try:
            # Словарь сокращений для лучших описаний
            abbreviations = {
                'BCU': 'Блок управления тормозами',
                'PST': 'Преобразователь статический тяговый',
                'PSN': 'Преобразователь статический низковольтный',
                'BUD': 'Блок управления дверьми',
                'TEMP': 'Температура',
                'PRESSURE': 'Давление',
                'VOLTAGE': 'Напряжение',
                'CURRENT': 'Ток',
                'SPEED': 'Скорость',
                'READY': 'Готовность',
                'FAULT': 'Неисправность',
                'STATUS': 'Состояние'
            }

            parts = signal_code.split('_')
            if len(parts) > 1:
                description_parts = []
                for part in parts[1:]:  # Пропускаем тип сигнала
                    if not part.isdigit():  # Пропускаем номера
                        # Проверяем сокращения
                        expanded = abbreviations.get(part.upper(), part)
                        description_parts.append(expanded.title())

                if description_parts:
                    return ' '.join(description_parts)

            # Fallback с обработкой сокращений
            cleaned_code = signal_code.replace('_', ' ')
            for abbr, expansion in abbreviations.items():
                cleaned_code = cleaned_code.replace(abbr, expansion)
            
            return cleaned_code.title()

        except Exception:
            return signal_code.replace('_', ' ').title()

    def _determine_line_enhanced(self, signal_type: str) -> str:
        """РАСШИРЕННОЕ определение линии по типу сигнала"""
        line_mapping = {
            'B': 'L_CAN_BLOK_CH',
            'BY': 'L_CAN_ICU_CH_A', 
            'W': 'L_TV_MAIN_CH_A',
            'DW': 'L_TV_MAIN_CH_B',
            'F': 'L_LCUP_CH_A',
            'WF': 'L_LCUP_CH_B',
            'S': 'L_SYSTEM',
            'D': 'L_DIAGNOSTIC'
        }
        return line_mapping.get(signal_type, 'L_UNKNOWN')

    def _extract_wagon_number_enhanced(self, signal_code: str) -> str:
        """РАСШИРЕННОЕ извлечение номера вагона"""
        try:
            parts = signal_code.split('_')
            for part in reversed(parts):
                if part.isdigit():
                    num = int(part)
                    if 1 <= num <= 16:  # Расширили диапазон
                        return str(num)
            
            # Дополнительная проверка для других форматов
            wagon_match = re.search(r'[Ww](\d+)', signal_code)
            if wagon_match:
                return wagon_match.group(1)
                
            return '1'  # По умолчанию первый вагон
            
        except Exception:
            return '1'

    def _determine_data_type(self, signal_code: str) -> str:
        """НОВЫЙ МЕТОД: Определение типа данных по коду сигнала"""
        try:
            signal_type = signal_code.split('_')[0] if '_' in signal_code else signal_code
            
            type_mapping = {
                'B': 'BOOL',
                'BY': 'BYTE', 
                'W': 'WORD',
                'DW': 'DWORD',
                'F': 'FLOAT',
                'WF': 'FLOAT',
                'S': 'STRING'
            }
            
            return type_mapping.get(signal_type, 'UNKNOWN')
            
        except Exception:
            return 'UNKNOWN'

    def _is_problematic_parameter(self, signal_code: str, description: str) -> bool:
        """НОВЫЙ МЕТОД: Определение проблемных параметров"""
        try:
            problematic_indicators = [
                'FAULT', 'ERROR', 'FAIL', 'ALARM', 'WARNING',
                'НЕИСПРАВНОСТЬ', 'ОШИБКА', 'АВАРИЯ', 'ПРЕДУПРЕЖДЕНИЕ'
            ]
            
            combined_text = f"{signal_code} {description}".upper()
            return any(indicator in combined_text for indicator in problematic_indicators)
            
        except Exception:
            return False

    def _extract_lines_enhanced(self, parameters: List[Dict[str, Any]]) -> set:
        """РАСШИРЕННОЕ извлечение уникальных линий"""
        try:
            lines = {param['line'] for param in parameters if param.get('line')}
            
            # Добавляем системные линии если их нет
            default_lines = {'L_CAN_BLOK_CH', 'L_CAN_ICU_CH_A', 'L_TV_MAIN_CH_A'}
            lines.update(default_lines)
            
            return lines
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения линий: {e}")
            return set()

    def _collect_load_statistics_enhanced(self, file_path: str, load_time: float, 
                                        df: pd.DataFrame, metadata: Dict[str, str]):
        """РАСШИРЕННЫЙ сбор статистики загрузки"""
        try:
            self._load_statistics = {
                'file_path': file_path,
                'load_time_seconds': load_time,
                'timestamp': datetime.now().isoformat(),
                'data_shape': df.shape,
                'parameters_count': len(self.parameters),
                'lines_count': len(self.lines),
                'potentially_changed_count': sum(1 for p in self.parameters if p.get('is_potentially_changed', False)),
                'problematic_count': sum(1 for p in self.parameters if p.get('is_problematic', False)),
                'metadata_fields': list(metadata.keys()),
                'has_real_timestamp': 'real_timestamp' in metadata,
                'sampling_period_ms': metadata.get('sampling_period_ms', 'unknown'),
                'vehicle_number': metadata.get('vehicle_number', 'unknown')
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора статистики загрузки: {e}")

    def filter_changed_params(self, start_time, end_time, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """ПРИОРИТЕТНАЯ фильтрация изменяемых параметров для интеграции с main_controller.py"""
        try:
            from datetime import datetime

            # Преобразование строк в datetime если необходимо
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

            self.logger.info(f"ПРИОРИТЕТНАЯ фильтрация изменяемых параметров: {start_time} - {end_time}")

            if not hasattr(self, 'data') or self.data is None:
                self.logger.warning("Нет данных для фильтрации")
                return []

            changed_params = []
            
            for param in self.parameters:
                try:
                    signal_code = param.get('signal_code', '').upper()
                    
                    # Исключаем системные параметры
                    if any(sys_word in signal_code for sys_word in ['TIMESTAMP', 'DATE', 'TIME', 'INDEX']):
                        continue
                    
                    # ПРИОРИТЕТНАЯ проверка: используем предварительную оценку
                    if param.get('is_potentially_changed', False):
                        # Дополнительная проверка с threshold если данные доступны
                        column_name = param.get('full_column', signal_code)
                        if column_name in self.data.columns:
                            series = self.data[column_name]
                            if self._detailed_change_analysis(series, threshold):
                                changed_params.append(param)
                        else:
                            # Если данных нет, но предварительная оценка положительная
                            changed_params.append(param)
                    
                except Exception as e:
                    self.logger.debug(f"Ошибка анализа параметра {param}: {e}")
                    continue

            self.logger.info(f"Найдено {len(changed_params)} изменяемых параметров из {len(self.parameters)}")
            return changed_params

        except Exception as e:
            self.logger.error(f"Ошибка приоритетной фильтрации изменяемых параметров: {e}")
            return []

    def _detailed_change_analysis(self, series: pd.Series, threshold: float) -> bool:
        """НОВЫЙ МЕТОД: Детальный анализ изменяемости с threshold"""
        try:
            clean_series = series.dropna()
            
            if len(clean_series) < 2:
                return False
            
            # Для числовых данных
            if clean_series.dtype.kind in 'biufc':
                # Проверяем коэффициент вариации
                if clean_series.std() > 0:
                    cv = clean_series.std() / abs(clean_series.mean()) if clean_series.mean() != 0 else float('inf')
                    if cv > threshold:
                        return True
                
                # Проверяем отношение уникальных значений
                unique_ratio = len(clean_series.unique()) / len(clean_series)
                return unique_ratio > threshold
            
            # Для категориальных данных
            unique_count = len(clean_series.unique())
            total_count = len(clean_series)
            
            # Должно быть изменение, но не слишком много уникальных значений
            return 1 < unique_count < total_count * 0.8

        except Exception:
            return False

    def get_load_statistics(self) -> Dict[str, Any]:
        """НОВЫЙ МЕТОД: Получение статистики загрузки"""
        return self._load_statistics.copy()

    def cleanup(self):
        """НОВЫЙ МЕТОД: Очистка ресурсов"""
        try:
            self._clear_previous_data()
            self._encoding_cache.clear()
            self._structure_cache.clear()
            self._load_statistics.clear()
            self.logger.info("CSVDataLoader очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки CSVDataLoader: {e}")

    def __str__(self):
        return f"CSVDataLoader(params={len(self.parameters)}, lines={len(self.lines)}, records={self.records_count})"

    def __repr__(self):
        return self.__str__()
