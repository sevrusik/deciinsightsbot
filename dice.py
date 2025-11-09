# dice.py - Dice System
"""
Система виртуальных кубиков для сторителлинга
"""

import random
from typing import Dict, List, Tuple
from dice_meanings import get_all_symbols


class DiceSystem:
    """Система кубиков с символами из BASIC_SYMBOLS"""

    def __init__(self):
        # Используем символы из dice_meanings.py
        self.symbols = get_all_symbols()
        # Старые архетипы и эмоции убраны, теперь только символы
        self.archetypes = []
        self.emotions = []

    def roll_dice(self, count: int = 3) -> List[str]:
        """
        Бросить кубики

        Args:
            count: количество кубиков (по умолчанию 3)

        Returns:
            list: список выпавших символов, например ["🔍", "🎩", "✏️"]
        """
        return random.sample(self.symbols, min(count, len(self.symbols)))

    def format_result(self, symbols: List[str]) -> str:
        """
        Форматировать результат броска для отображения

        Args:
            symbols: список выпавших символов

        Returns:
            str: отформатированная строка
        """
        result = "🎲 **Результат броска:**\n\n"
        for i, symbol in enumerate(symbols, 1):
            result += f"{symbol} "
        return result.strip()



# Глобальный экземпляр системы кубиков
dice_system = DiceSystem()
