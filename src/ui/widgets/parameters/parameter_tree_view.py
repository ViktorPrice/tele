"""
Исправленное представление дерева параметров с корректными сообщениями и обработкой ошибок
"""

import logging
from typing import List, Any, Union

# Предполагается, что tree_widget - это объект с методами get_children, delete, insert,
# например tkinter.ttk.Treeview. Для универсальности типизация не конкретизирована.
class ParameterTreeView:
    """Исправленное представление дерева параметров"""

    def __init__(self, tree_widget: Any):
        """
        Инициализация с виджетом дерева.

        :param tree_widget: виджет дерева с методами get_children, delete, insert
        """
        self.tree = tree_widget
        self.logger = logging.getLogger(self.__class__.__name__)

    def update_tree(self, params: List[Union[dict, list, tuple]]):
        """
        ИСПРАВЛЕННОЕ обновление дерева с корректными сообщениями.

        :param params: список параметров, каждый из которых может быть dict с ключами
                       'signal_code', 'description', 'line', 'wagon' или список/кортеж с минимум 4 элементами
        """
        try:
            self.logger.info(f"Обновление дерева: получено {len(params)} параметров")

            if not params:
                self.logger.warning("Нет параметров для отображения")
                self._show_empty_message()
                return

            # Очищаем существующие данные
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Добавляем новые данные
            added_count = 0
            for param in params:
                try:
                    if isinstance(param, dict):
                        values = (
                            param.get('signal_code', ''),
                            param.get('description', ''),
                            param.get('line', ''),
                            param.get('wagon', '')
                        )
                    elif isinstance(param, (tuple, list)) and len(param) >= 4:
                        values = tuple(param[:4])
                    else:
                        self.logger.warning(f"Пропущен некорректный параметр: {param}")
                        continue

                    self.tree.insert('', 'end', values=values)
                    added_count += 1

                except Exception as e:
                    self.logger.error(f"Ошибка добавления параметра: {e}")
                    continue

            self.logger.info(f"Добавлено {added_count} параметров в дерево")

        except Exception as e:
            self.logger.error(f"Ошибка обновления дерева: {e}")

    def _show_empty_message(self):
        """
        Показ сообщения о пустом дереве.
        Очищает дерево и добавляет информационную строку.
        """
        # Очищаем дерево
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Добавляем информационное сообщение
        self.tree.insert('', 'end', values=('Нет данных', 'Загрузите CSV файл', '', ''))
