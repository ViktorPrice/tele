"""
Конфигурация линий связи
"""
from typing import Dict
import json
import logging
from pathlib import Path

class LineConfig:
    """Конфигурация линий связи"""
    
    def __init__(self, config_file: str = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file
        self._line_comments = self._load_default_comments()
        
        if config_file:
            self._load_from_file(config_file)
    
    def _load_default_comments(self) -> Dict[str, str]:
        """Загрузка комментариев по умолчанию"""
        return {
            'L_LCU_BIM1_CH': 'БИМ1',
            'L_LCU_BIM2_CH': 'БИМ2',
            'T_TV_MAIN_CH_A': 'MAIN A',
            'T_TV_MAIN_CH_B': 'MAIN B',
            'L_CAN_BLOK_CH': 'BLOK',
            'L_CAN_ICU_CH_A': 'CAN A',
            'L_CAN_ICU_CH_B': 'CAN B',
            'L_TV_MAIN_CH_A': 'ТВ A',
            'L_TV_MAIN_CH_B': 'ТВ B',
            'L_LCUP_CH_A': 'LCUP A',
            'L_LCUP_CH_B': 'LCUP B',
            'L_REC_CH_A': 'REC A',
            'L_REC_CH_B': 'REC B',
            'L_CAN_POS_CH': 'CAN POS'
        }
    
    def _load_from_file(self, file_path: str) -> None:
        """Загрузка конфигурации из файла"""
        try:
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'line_comments' in config:
                    self._line_comments.update(config['line_comments'])
                
                self.logger.info(f"Конфигурация линий загружена из {file_path}")
            else:
                self.logger.info(f"Файл конфигурации {file_path} не найден, используются значения по умолчанию")
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации линий: {e}")
    
    def get_line_comments(self) -> Dict[str, str]:
        """Получение комментариев для линий"""
        return self._line_comments.copy()
    
    def get_line_comment(self, line_name: str) -> str:
        """Получение комментария для конкретной линии"""
        return self._line_comments.get(line_name, line_name)
    
    def add_line_comment(self, line_name: str, comment: str) -> None:
        """Добавление комментария для линии"""
        self._line_comments[line_name] = comment
        self.logger.info(f"Добавлен комментарий для линии {line_name}")
    
    def save_to_file(self, file_path: str = None) -> bool:
        """Сохранение конфигурации в файл"""
        try:
            target_file = file_path or self.config_file
            if not target_file:
                self.logger.error("Не указан файл для сохранения")
                return False
            
            config = {
                'line_comments': self._line_comments
            }
            
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Конфигурация линий сохранена в {target_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
            return False
