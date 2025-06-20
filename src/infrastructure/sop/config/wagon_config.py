"""
Конфигурация вагонов
"""
from typing import Dict, Optional
import logging

class WagonConfig:
    """Конфигурация номеров вагонов"""
    
    def __init__(self, data_loader=None):
        self.data_loader = data_loader
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Изначально пустая карта номеров вагонов
        self._wagon_number_map = {}
        
        # Кэш управляющего вагона
        self._controlling_wagon_cache: Optional[int] = None
    
    def get_wagon_number_map(self) -> Dict[int, str]:
        """Получение карты номеров вагонов"""
        return self._wagon_number_map.copy()
    
    def get_controlling_wagon(self) -> Optional[int]:
        """Определение управляющего вагона с кэшированием"""
        if self._controlling_wagon_cache is not None:
            return self._controlling_wagon_cache
        
        if self.data_loader:
            self._controlling_wagon_cache = self.data_loader.get_controlling_wagon()
        
        return self._controlling_wagon_cache or 1  # По умолчанию первый вагон
    
    def get_real_wagon_number(self, skvoz_num: int) -> str:
        """Преобразование сквозного номера в реальный"""
        leading_wagon = self.get_controlling_wagon()
        
        if leading_wagon == 1:
            self._wagon_number_map = {
                1: "1г", 2: "11бо", 3: "2м", 4: "3нм", 5: "6м",
                6: "8м", 7: "7нм", 8: "12м", 9: "13бо", 10: "10м", 11: "9г"
            }
        elif leading_wagon == 9:
            self._wagon_number_map = {
                11: "1г", 10: "11бо", 9: "2м", 8: "3нм", 7: "6м",
                6: "8м", 5: "7нм", 4: "12м", 3: "13бо", 2: "10м", 1: "9г"
            }
        else:
            # По умолчанию используем стандартную карту сдвига
            offset = leading_wagon - 1 if leading_wagon else 0
            adjusted_num = ((skvoz_num - 1 + offset) % 11) + 1
            return self._wagon_number_map.get(adjusted_num, str(skvoz_num))
        
        # Если карта обновлена, возвращаем значение из неё
        return self._wagon_number_map.get(skvoz_num, str(skvoz_num))
    
    def update_wagon_map(self, new_map: Dict[int, str]) -> None:
        """Обновление карты номеров вагонов"""
        self._wagon_number_map.update(new_map)
        self.logger.info("Карта номеров вагонов обновлена")
    
    def reset_controlling_wagon_cache(self) -> None:
        """Сброс кэша управляющего вагона"""
        self._controlling_wagon_cache = None
