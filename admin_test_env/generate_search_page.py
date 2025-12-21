"""
Корпоративный поисковик для локальной сети
Версия: 1.0.0

Главный скрипт для генерации поисковой страницы.
Запускается администратором для обновления индекса файлов.
"""

import os
import sys
import json
import configparser
from datetime import datetime
from pathlib import Path

def should_index_file(filename, extensions):
    """
    Проверяет, нужно ли индексировать файл по расширению
    
    Args:
        filename (str): Имя файла
        extensions (list): Список расширений для индексации
        
    Returns:
        bool: True если файл нужно индексировать
    """
    if not filename:
        return False
    
    # Извлекаем расширение
    name_parts = filename.lower().split('.')
    if len(name_parts) < 2:
        return False  # Нет расширения
    
    ext = name_parts[-1]
    return ext in extensions

def scan_directory(directory_path, file_extensions, max_files, current_count):
    """
    Рекурсивно сканирует каталог и возвращает список файлов
    
    Args:
        directory_path (str): Путь к каталогу для сканирования
        file_extensions (list): Список расширений для индексации
        max_files (int): Максимальное количество файлов для индексации
        current_count (list): Счетчик файлов в формате [count] для модификации
        
    Returns:
        list: Список относительных путей файлов
    """
    files_found = []
    
    try:
        for root, dirs, filenames in os.walk(directory_path):
            # Пропускаем скрытые каталоги
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                # Проверяем ограничение по количеству файлов
                if max_files > 0 and current_count[0] >= max_files:
                    print(f"⚠️  Достигнут лимит в {max_files} файлов. Сканирование остановлено.")
                    return files_found
                
                # Проверяем расширение файла
                if should_index_file(filename, file_extensions):
                    # Получаем относительный путь от сканируемого каталога
                    full_path = os.path.join(root, filename)
                    try:
                        rel_path = os.path.relpath(full_path, directory_path)
                        # Нормализуем разделители путей
                        rel_path = rel_path.replace('\\', '/')
                        files_found.append(rel_path)
                        current_count[0] += 1
                    except ValueError:
                        # Если пути на разных дисках (Windows)
                        print(f"⚠️  Не удалось получить относительный путь для: {full_path}")
                        continue
                
                # Выводим прогресс каждые 1000 файлов
                if current_count[0] % 1000 == 0:
                    print(f"  Просканировано файлов: {current_count[0]}")
    
    except PermissionError:
        print(f"❌ Ошибка доступа к каталогу: {directory_path}")
    except Exception as e:
        print(f"❌ Ошибка при сканировании {directory_path}: {e}")
    
    return files_found

def normalize_path_separators(path):
    """
    Нормализует разделители путей для кроссплатформенности
    
    Args:
        path (str): Путь с разделителями
        
    Returns:
        str: Путь с универсальными разделителями (/)
    """
    if not path:
        return path
    
    # Заменяем обратные слеши на прямые
    normalized = path.replace('\\', '/')
    
    # Убираем двойные слеши
    while '//' in normalized:
        normalized = normalized.replace('//', '/')
    
    return normalized

def split_path_and_filename(full_path):
    """
    Разделяет полный путь на путь и имя файла
    
    Args:
        full_path (str): Полный путь к файлу
        
    Returns:
        dict: {'path': путь, 'filename': имя файла}
    """
    if not full_path:
        return {'path': '', 'filename': ''}
    
    # Нормализуем разделители
    normalized_path = normalize_path_separators(full_path)
    
    # Находим последний разделитель
    last_slash = normalized_path.rfind('/')
    
    if last_slash == -1:
        # Файл в корне каталога
        return {'path': '', 'filename': normalized_path}
    
    path_part = normalized_path[:last_slash]
    filename_part = normalized_path[last_slash + 1:]
    
    return {'path': path_part, 'filename': filename_part}

def build_file_index(scan_directories, file_extensions, max_files):
    """
    Строит индекс файлов для всех каталогов сканирования
    
    Args:
        scan_directories (list): Список кортежей (путь, короткое_имя)
        file_extensions (list): Список расширений для индексации
        max_files (int): Максимальное количество файлов для индексации
        
    Returns:
        tuple: (список каталогов, список файлов, статистика)
    """
    print("📁 Начинаем построение индекса файлов...")
    
    # Структуры данных для JavaScript
    scan_dirs_data = []  # [id, короткое_имя, полный_путь]
    file_index_data = []  # [id_каталога, относительный_путь_файла]
    
    total_files_scanned = [0]  # Используем список для модификации в функции
    
    # Обрабатываем каждый каталог сканирования
    for dir_id, (dir_path, dir_name) in enumerate(scan_directories):
        print(f"\n📂 Сканируем каталог: {dir_name} ({dir_path})")
        
        # Проверяем существование каталога
        if not os.path.exists(dir_path):
            print(f"❌ Каталог не существует: {dir_path}")
            continue
        if not os.path.isdir(dir_path):
            print(f"❌ Указанный путь не является каталогом: {dir_path}")
            continue
        
        # Добавляем каталог в данные
        scan_dirs_data.append([dir_id, dir_name, dir_path])
        
        # Сканируем файлы в каталоге
        files_in_dir = scan_directory(
            dir_path, 
            file_extensions, 
            max_files, 
            total_files_scanned
        )
        
        # Добавляем файлы в индекс
        for file_path in files_in_dir:
            file_index_data.append([dir_id, file_path])
        
        print(f"  Найдено файлов в каталоге: {len(files_in_dir)}")
        
        # Проверяем лимит по файлам
        if max_files > 0 and total_files_scanned[0] >= max_files:
            print(f"\n⚠️  Достигнут общий лимит в {max_files} файлов.")
            break
    
    # Статистика
    stats = {
        'total_directories': len(scan_dirs_data),
        'total_files': len(file_index_data),
        'max_files_limit': max_files,
        'file_extensions': file_extensions
    }
    
    print(f"\n✅ Индекс построен:")
    print(f"   • Каталогов: {stats['total_directories']}")
    print(f"   • Файлов: {stats['total_files']}")
    print(f"   • Расширения: {', '.join(file_extensions)}")
    
    return scan_dirs_data, file_index_data, stats

def load_configuration():
    """
    Загружает и проверяет конфигурацию из config.ini
    
    Returns:
        dict: Конфигурационные данные или None при ошибке
    """
    # Проверяем существование конфигурационного файла
    if not os.path.exists('config.ini'):
        print("\n❌ Ошибка: Файл config.ini не найден.")
        print("\nИнструкция для администратора:")
        print("1. Создайте файл config.ini в той же папке")
        print("2. Настройте его по примеру из документации")
        print("3. Запустите скрипт снова")
        print("\nПример config.ini:")
        print("[PATHS]")
        print("scan_directories = путь:Имя, путь:Имя")
        print("output_path = путь/search.html")
        print("[SETTINGS]")
        print("file_extensions = pdf,doc,docx")
        print("max_files = 200000")
        return None
    
    try:
        # Загружаем конфигурацию
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        
        # Проверяем обязательные секции
        if not config.has_section('PATHS'):
            raise ValueError("Отсутствует секция [PATHS] в config.ini")
        if not config.has_section('SETTINGS'):
            raise ValueError("Отсутствует секция [SETTINGS] в config.ini")
        
        # Читаем настройки
        scan_dirs_str = config.get('PATHS', 'scan_directories', fallback='')
        output_path = config.get('PATHS', 'output_path', fallback='')
        menu_file_path = config.get('PATHS', 'menu_file_path', fallback='')
        
        max_files = config.getint('SETTINGS', 'max_files', fallback=200000)
        results_per_page = config.getint('SETTINGS', 'results_per_page', fallback=10)
        extensions_str = config.get('SETTINGS', 'file_extensions', fallback='')
        config_version = config.get('SETTINGS', 'config_version', fallback='1.0')
        
        # Парсим каталоги для сканирования
        scan_directories = []
        if scan_dirs_str:
            for item in scan_dirs_str.split(','):
                item = item.strip()
                if not item:
                    continue
                    
                if ':' in item:
                    path, name = item.split(':', 1)
                    scan_directories.append((path.strip(), name.strip()))
                else:
                    path = item.strip()
                    name = os.path.basename(path.rstrip('/\\'))
                    scan_directories.append((path, name))
        
        # Парсим расширения файлов
        file_extensions = [ext.strip().lower() for ext in extensions_str.split(',') if ext.strip()]
        
        config_data = {
            'scan_directories': scan_directories,
            'output_path': output_path,
            'menu_file_path': menu_file_path if menu_file_path else None,
            'max_files': max_files,
            'results_per_page': results_per_page,
            'file_extensions': file_extensions,
            'config_version': config_version
        }
        
        print(f"\n📋 Загруженная конфигурация:")
        print(f"   • Каталогов для сканирования: {len(scan_directories)}")
        print(f"   • Выходной файл: {output_path}")
        print(f"   • Макс. файлов: {max_files}")
        print(f"   • Расширения: {', '.join(file_extensions[:5])}{'...' if len(file_extensions) > 5 else ''}")
        
        return config_data
        
    except Exception as e:
        print(f"\n❌ Ошибка загрузки конфигурации: {e}")
        print("\nПроверьте правильность заполнения config.ini")
        return None

def generate_html_page(template_path, output_path, scan_dirs_data, file_index_data, stats, menu_file_path=None):
    """
    Генерирует HTML страницу поиска
    
    Args:
        template_path (str): Путь к шаблону HTML
        output_path (str): Куда сохранить результат
        scan_dirs_data (list): Данные каталогов
        file_index_data (list): Индекс файлов
        stats (dict): Статистика
        menu_file_path (str): Путь к файлу меню (опционально)
        
    Returns:
        bool: True если успешно
    """
    print(f"\n📄 Генерация HTML страницы...")
    
    try:
        # TODO: Реализовать чтение шаблона и вставку данных
        # Это будет на следующем этапе
        print(f"   • Шаблон: {template_path}")
        print(f"   • Выходной файл: {output_path}")
        print(f"   • Данные для вставки: {len(file_index_data)} файлов")
        
        # Пока просто сообщаем, что этот этап еще не реализован
        print("⚠️  Внимание: Генерация HTML еще не реализована")
        print("   Этот этап будет выполнен позже")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка генерации HTML: {e}")
        return False

def main():
    """Основная функция скрипта"""
    print("=" * 50)
    print("Поисковик для локальной сети - Генератор страницы")
    print("=" * 50)
    
    # Загружаем конфигурацию
    config_data = load_configuration()
    if not config_data:
        return 1
    
    # Проверяем обязательные параметры
    try:
        if not config_data['scan_directories']:
            raise ValueError("Не указаны каталоги для сканирования (scan_directories)")
        if not config_data['output_path']:
            raise ValueError("Не указан выходной файл (output_path)")
        if not config_data['file_extensions']:
            raise ValueError("Не указаны расширения файлов (file_extensions)")
    except ValueError as e:
        print(f"\n❌ Ошибка: {e}")
        return 1
    
    # Строим индекс файлов
    scan_dirs_data, file_index_data, stats = build_file_index(
        config_data['scan_directories'], 
        config_data['file_extensions'], 
        config_data['max_files']
    )
    
    # Проверяем, что есть что индексировать
    if not scan_dirs_data:
        print("\n❌ Ошибка: Не удалось просканировать ни один каталог")
        print("   Проверьте пути в config.ini")
        return 1
    
    if not file_index_data:
        print("\n⚠️  Предупреждение: Не найдено файлов для индексации")
        print("   Проверьте расширения файлов в config.ini")
    
    # Генерируем HTML страницу
    # TODO: Реализовать когда будут готовы template.html и другие файлы
    # success = generate_html_page(
    #     'template.html',
    #     config_data['output_path'],
    #     scan_dirs_data,
    #     file_index_data,
    #     stats,
    #     config_data['menu_file_path']
    # )
    
    # Временно просто сообщаем об успехе индексации
    print(f"\n✅ Индексация завершена успешно!")
    print(f"   • Файлов в индексе: {stats['total_files']}")
    print(f"   • Каталогов: {stats['total_directories']}")
    print(f"\nℹ️  HTML страница будет сгенерирована на следующем этапе")
    print(f"   Выходной файл: {config_data['output_path']}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)