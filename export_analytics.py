#!/usr/bin/env python3
# export_analytics.py - Export analytics to CSV
"""
Скрипт для экспорта аналитики в CSV файлы
Использование: python export_analytics.py
"""

import csv
from datetime import datetime
from database import get_stats, get_detailed_analytics, get_db, User, DiceThrow

def export_stats_to_csv():
    """Экспорт статистики в CSV"""
    stats = get_stats()
    analytics = get_detailed_analytics()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Основная статистика
    with open(f'stats_summary_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Метрика', 'Значение'])
        writer.writerow(['Всего пользователей', stats['users']])
        writer.writerow(['Активных за 7 дней', stats['active_users_7d']])
        writer.writerow(['Всего бросков', stats['throws']])
        writer.writerow(['Завершённых бросков', stats['completed_throws']])
        writer.writerow(['Процент завершения', f"{stats['completion_rate']}%"])
        writer.writerow(['Среднее бросков/пользователь', stats['avg_throws_per_user']])
        writer.writerow(['Retention rate', f"{analytics['retention_rate']}%"])
        writer.writerow(['Вернувшихся пользователей', analytics['returning_users']])

    # 2. Пути
    with open(f'paths_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Путь', 'Количество', 'Процент'])
        for path, count in stats['path_distribution'].items():
            percentage = (count / stats['completed_throws'] * 100) if stats['completed_throws'] > 0 else 0
            writer.writerow([path, count, f"{percentage:.1f}%"])

    # 3. Пользователи по дням
    with open(f'users_by_day_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Дата', 'Новых пользователей'])
        for item in analytics['users_by_day']:
            writer.writerow([item['date'], item['count']])

    # 4. Броски по дням
    with open(f'throws_by_day_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Дата', 'Бросков'])
        for item in analytics['throws_by_day']:
            writer.writerow([item['date'], item['count']])

    # 5. Детальные данные пользователей
    db = get_db()
    try:
        users = db.query(User).all()
        with open(f'users_detail_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Telegram ID', 'Username', 'Full Name', 'Created At', 'Last Interaction', 'Total Throws'])
            for user in users:
                throw_count = db.query(DiceThrow).filter(DiceThrow.user_id == user.id).count()
                writer.writerow([
                    user.telegram_id,
                    user.username or '',
                    user.full_name or '',
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    user.last_interaction.strftime('%Y-%m-%d %H:%M:%S'),
                    throw_count
                ])
    finally:
        db.close()

    print(f"✅ Экспорт завершён! Файлы:")
    print(f"   - stats_summary_{timestamp}.csv")
    print(f"   - paths_{timestamp}.csv")
    print(f"   - users_by_day_{timestamp}.csv")
    print(f"   - throws_by_day_{timestamp}.csv")
    print(f"   - users_detail_{timestamp}.csv")


if __name__ == "__main__":
    export_stats_to_csv()
