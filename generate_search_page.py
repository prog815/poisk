"""
Корпоративный поисковик для локальной сети
Версия: 1.0.3

Главный скрипт для генерации поисковой страницы.
Запускается администратором для обновления индекса файлов.
"""

VERSION = "1.0.3"

import os
import sys
import json
import configparser
from datetime import datetime
from pathlib import Path


def convert_to_relative_paths(scan_dirs_data, output_path):
    """
    Преобразует абсолютные пути в scan_dirs_data в относительные
    относительно директории output_path
    """
    output_dir = os.path.dirname(output_path)
    relative_dirs = []
    
    for dir_id, dir_name, abs_path in scan_dirs_data:
        try:
            # Вычисляем относительный путь от output_dir к каталогу сканирования
            rel_path = os.path.relpath(abs_path, output_dir)
            # Для HTML заменяем обратные слеши на прямые
            rel_path = rel_path.replace('\\', '/')
            relative_dirs.append([dir_id, dir_name, rel_path])
        except ValueError as e:
            print(f"⚠️  Не удалось вычислить относительный путь для {abs_path}: {e}")
            # Если не получается, оставляем абсолютный
            relative_dirs.append([dir_id, dir_name, abs_path])
    
    return relative_dirs

# ===== ФУНКЦИИ ИНДЕКСАЦИИ =====

def should_index_file(filename, extensions):
    """
    Проверяет, нужно ли индексировать файл по расширению
    Не меняет регистр имени файла
    """
    if not filename:
        return False
    
    name_parts = filename.split('.')  # УБИРАЕМ .lower() здесь!
    if len(name_parts) < 2:
        return False
    
    ext = name_parts[-1].lower()  # Проверяем расширение в нижнем регистре
    return ext in extensions

def scan_directory(directory_path, file_extensions, max_files, current_count):
    """
    Рекурсивно сканирует каталог и возвращает список файлов
    Возвращает оригинальные пути ОТНОСИТЕЛЬНО directory_path
    """
    files_found = []
    
    try:
        for root, dirs, filenames in os.walk(directory_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if max_files > 0 and current_count[0] >= max_files:
                    print(f"⚠️  Достигнут лимит в {max_files} файлов.")
                    return files_found
                
                if should_index_file(filename, file_extensions):
                    full_path = os.path.join(root, filename)
                    try:
                        # Сохраняем ОРИГИНАЛЬНЫЙ путь (регистр, пробелы и т.д.)
                        rel_to_dir = os.path.relpath(full_path, directory_path)
                        rel_to_dir = rel_to_dir.replace('\\', '/')  # только слеши меняем
                        files_found.append(rel_to_dir)  # оригинальный регистр
                        current_count[0] += 1
                    except ValueError as e:
                        print(f"⚠️  Не удалось получить относительный путь: {full_path}")
                        print(f"     Ошибка: {e}")
                        continue
                    except Exception as e:
                        print(f"⚠️  Ошибка при обработке пути {full_path}: {e}")
                        continue
                
                if current_count[0] % 1000 == 0:
                    print(f"  Просканировано файлов: {current_count[0]}")
    
    except PermissionError:
        print(f"❌ Ошибка доступа к каталогу: {directory_path}")
    except Exception as e:
        print(f"❌ Ошибка при сканировании {directory_path}: {e}")
    
    return files_found

def build_file_index(scan_directories, file_extensions, max_files, output_path=None):
    """
    Строит индекс файлов для всех каталогов сканирования
    Возвращает пути ОТНОСИТЕЛЬНО каждого каталога сканирования
    output_path: если указан, пути в scanDirs будут относительными к output_path
    """
    print("📁 Начинаем построение индекса файлов...")
    
    scan_dirs_data = []
    file_index_data = []
    total_files_scanned = [0]
    
    for dir_id, (dir_path, dir_name) in enumerate(scan_directories):
        print(f"\n📂 Сканируем каталог: {dir_name} ({dir_path})")
        
        if not os.path.exists(dir_path):
            print(f"❌ Каталог не существует: {dir_path}")
            continue
        if not os.path.isdir(dir_path):
            print(f"❌ Указанный путь не является каталогом: {dir_path}")
            continue
        
        # ===== ИСПРАВЛЕННЫЙ БЛОК: относительные пути от output_path =====
        if output_path:
            try:
                # Ключевое исправление: вычисляем относительно директории output_path
                # НЕ относительно текущей директории скрипта!
                
                # Получаем абсолютный путь к директории output
                if os.path.isabs(output_path):
                    output_dir = os.path.dirname(output_path)
                else:
                    # Если путь относительный, делаем его относительно текущей директории
                    output_dir = os.path.dirname(os.path.abspath(output_path))
                
                print(f"  • Директория search.html: {output_dir}")
                
                # Получаем абсолютный путь к каталогу сканирования
                abs_scan_dir = os.path.abspath(dir_path)
                print(f"  • Каталог сканирования: {abs_scan_dir}")
                
                # Вычисляем относительный путь ОТ output_dir К abs_scan_dir
                rel_path = os.path.relpath(abs_scan_dir, output_dir)
                
                print(f"  • Вычисляю: os.path.relpath({abs_scan_dir}, {output_dir})")
                print(f"  • Результат: {rel_path}")
                
                rel_path = rel_path.replace('\\', '/')
                scan_dirs_data.append([dir_id, dir_name, rel_path])
                
            except Exception as e:
                print(f"⚠️  Ошибка относительного пути для {dir_path}: {e}")
                print(f"   • Тип ошибки: {type(e).__name__}")
                # В случае ошибки используем короткое имя каталога
                scan_dirs_data.append([dir_id, dir_name, dir_name])
        else:
            scan_dirs_data.append([dir_id, dir_name, dir_path])
        # ===== КОНЕЦ ИСПРАВЛЕННОГО БЛОКА =====
        
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
        
        print(f"  • Найдено файлов в каталоге: {len(files_in_dir)}")
        
        if max_files > 0 and total_files_scanned[0] >= max_files:
            print(f"\n⚠️  Достигнут общий лимит в {max_files} файлов.")
            break
    
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

# ===== ФУНКЦИИ ГЕНЕРАЦИИ HTML =====

def read_file_content(file_path):
    """
    Читает содержимое файла
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла {file_path}: {e}")
        return ""

def generate_menu_iframe(menu_file_path, output_path):
    """
    Генерирует HTML-код для iFrame с меню
    """
    if not menu_file_path or not os.path.exists(menu_file_path):
        return ''
    
    try:
        output_dir = os.path.dirname(output_path)
        relative_path = os.path.relpath(menu_file_path, output_dir)
        relative_path = relative_path.replace('\\', '/')
        
        return f'''
        <div id="menu-container">
            <iframe src="{relative_path}" 
                    frameborder="0" 
                    style="width:100%; height:auto; border:none;"
                    title="Меню сетевого диска">
            </iframe>
        </div>
        '''
    except Exception as e:
        print(f"❌ Ошибка при генерации меню: {e}")
        return ''

def generate_html_page(output_path, scan_dirs_data, file_index_data, stats, 
                       config_data, template_path='template.html', 
                       styles_path='styles.css', js_path='search.js'):
    """
    Генерирует HTML страницу поиска
    """
    print(f"\n📄 Генерация HTML страницы...")
    
    # ПРОВЕРКА ПУТЕЙ (добавьте этот блок)
    print("\n🔍 Проверка путей в индексе:")
    print(f"   Каталог вывода: {os.path.dirname(output_path)}")
    
    if file_index_data and len(file_index_data) > 0:
        print(f"   Примеры путей:")
        for i in range(min(3, len(file_index_data))):
            file = file_index_data[i]
            print(f"     - {file[1]}")
        if len(file_index_data) > 3:
            print(f"     ... и еще {len(file_index_data) - 3} файлов")
    
    # Проверяем наличие файлов
    if not os.path.exists(template_path):
        print(f"❌ Шаблон не найден: {template_path}")
        return False
    if not os.path.exists(styles_path):
        print(f"❌ Стили не найдены: {styles_path}")
        return False
    if not os.path.exists(js_path):
        print(f"❌ JavaScript не найден: {js_path}")
        return False
    
    try:
        # Читаем файлы
        print("   • Чтение шаблонов...")
        html_template = read_file_content(template_path)
        css_content = read_file_content(styles_path)
        js_content = read_file_content(js_path)
        
        if not html_template:
            print("❌ Шаблон HTML пустой")
            return False
        
        # Подготавливаем данные для JavaScript
        system_info = {
            'version': VERSION,
            'lastUpdated': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'totalFiles': len(file_index_data),
            'directories': len(scan_dirs_data),
            'extensions': config_data['file_extensions'],
            'resultsPerPage': config_data['results_per_page']
        }
        
        # Генерируем меню если нужно
        menu_html = ''
        if config_data.get('menu_file_path'):
            menu_html = generate_menu_iframe(
                config_data['menu_file_path'], 
                output_path
            )
        
        print("   • Замена плейсхолдеров...")
        
        # Заменяем плейсхолдеры в шаблоне
        html_content = html_template
        
        # 1. Вставляем CSS
        html_content = html_content.replace('/*STYLES_PLACEHOLDER*/', css_content)
        
        # 2. Вставляем JavaScript
        html_content = html_content.replace('/*JS_PLACEHOLDER*/', js_content)
        
        # 3. Вставляем системную информацию
        system_info_js = f'window.systemInfo = {json.dumps(system_info, ensure_ascii=False)};'
        html_content = html_content.replace('/*SYSTEM_INFO_PLACEHOLDER*/', system_info_js)
        
        # 4. Вставляем данные каталогов
        scan_dirs_js = f'window.scanDirs = {json.dumps(scan_dirs_data, ensure_ascii=False)};'
        html_content = html_content.replace('/*SCAN_DIRS_PLACEHOLDER*/', scan_dirs_js)
        
        # 5. Вставляем индекс файлов
        file_index_js = f'window.fileIndex = {json.dumps(file_index_data, ensure_ascii=False)};'
        html_content = html_content.replace('/*FILE_INDEX_PLACEHOLDER*/', file_index_js)
        
        # 6. Вставляем меню
        if '<!-- Меню будет вставлено здесь -->' in html_content:
            html_content = html_content.replace(
                '<!-- Меню будет вставлено здесь -->', 
                menu_html
            )
        elif '<div id="menuContainer">' in html_content:
            # Находим и заменяем содержимое menuContainer
            import re
            pattern = r'<div id="menuContainer">.*?</div>'
            replacement = f'<div id="menuContainer">{menu_html}</div>'
            html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
        
        # 7. Обновляем количество результатов на страницу в шаблоне
        if 'resultsPerPage' in html_content:
            html_content = html_content.replace(
                '<span id="resultsPerPage">10</span>',
                f'<span id="resultsPerPage">{config_data["results_per_page"]}</span>'
            )
        
        # Создаем директорию для выходного файла если нужно
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Сохраняем HTML файл
        print(f"   • Сохранение: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Проверяем размер файла
        file_size = os.path.getsize(output_path)
        print(f"   • Размер файла: {file_size / 1024 / 1024:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка генерации HTML: {e}")
        import traceback
        traceback.print_exc()
        return False

# ===== КОНФИГУРАЦИЯ =====

def load_configuration():
    """
    Загружает и проверяет конфигурацию из config.ini
    """
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
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        
        if not config.has_section('PATHS'):
            raise ValueError("Отсутствует секция [PATHS] в config.ini")
        if not config.has_section('SETTINGS'):
            raise ValueError("Отсутствует секция [SETTINGS] в config.ini")
        
        scan_dirs_str = config.get('PATHS', 'scan_directories', fallback='')
        output_path = config.get('PATHS', 'output_path', fallback='')
        menu_file_path = config.get('PATHS', 'menu_file_path', fallback='')
        
        max_files = config.getint('SETTINGS', 'max_files', fallback=200000)
        results_per_page = config.getint('SETTINGS', 'results_per_page', fallback=10)
        extensions_str = config.get('SETTINGS', 'file_extensions', fallback='')
        config_version = config.get('SETTINGS', 'config_version', fallback='1.0')
        
        scan_directories = []
        if scan_dirs_str:
            # Разделяем по запятым
            items = []
            current_item = ""
            in_item = False
            
            # Ручной парсинг для правильной обработки Windows путей
            for char in scan_dirs_str:
                if char == ',' and not in_item:
                    if current_item:
                        items.append(current_item.strip())
                        current_item = ""
                else:
                    current_item += char
                    if char == '\\':
                        in_item = True
                    elif char == ':' and in_item:
                        in_item = False
            
            if current_item:
                items.append(current_item.strip())
            
            # Обрабатываем каждый элемент
            for item in items:
                if not item:
                    continue
                
                # Определяем позицию разделителя "путь:имя"
                # Для Windows: C:\folder:Имя → двоеточие после \folder
                # Для Linux: /mnt/folder:Имя → двоеточие после /folder
                # Для сетевых путей: \\server\share:Имя → двоеточие после \share
                
                colon_pos = -1
                
                # Ищем двоеточие, которое НЕ является частью диска Windows (не сразу после буквы)
                for i in range(len(item)):
                    if item[i] == ':':
                        # Проверяем, не является ли это диском Windows
                        if i == 1 and len(item) > 1 and item[0].isalpha():
                            # Это диск Windows (C:, D: и т.д.) - пропускаем
                            continue
                        # Проверяем, что перед двоеточием не сетевая доля (\\server\share:)
                        if i > 1 and item[i-1] in '\\/' and item[i-2] in '\\/':
                            # Это сетевая доля - пропускаем
                            continue
                        colon_pos = i
                        break
                
                if colon_pos > 0:
                    path = item[:colon_pos].strip()
                    name = item[colon_pos + 1:].strip()
                else:
                    # Нет двоеточия для имени
                    path = item.strip()
                    name = os.path.basename(path.rstrip('/\\'))
                
                scan_directories.append((path, name))
        
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
        for path, name in scan_directories:
            print(f"     - {name}: {path}")
        print(f"   • Выходной файл: {output_path}")
        print(f"   • Макс. файлов: {max_files}")
        print(f"   • Расширения: {', '.join(file_extensions[:5])}{'...' if len(file_extensions) > 5 else ''}")
        
        return config_data
        
    except Exception as e:
        print(f"\n❌ Ошибка загрузки конфигурации: {e}")
        print("\nПроверьте правильность заполнения config.ini")
        import traceback
        traceback.print_exc()
        return None

# ===== ОСНОВНАЯ ФУНКЦИЯ =====

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
    
    # В функции main() перед build_file_index
    print(f"\n🔍 Отладка путей:")
    print(f"   • output_path из конфига: {config_data['output_path']}")
    print(f"   • Текущая директория: {os.getcwd()}")
    print(f"   • Абсолютный output_path: {os.path.abspath(config_data['output_path'])}")
    
    # Строим индекс файлов (пути относительно каталогов сканирования)
    scan_dirs_data, file_index_data, stats = build_file_index(
        config_data['scan_directories'], 
        config_data['file_extensions'], 
        config_data['max_files'],
        output_path=config_data['output_path']
    )
    
    # # ПРЕОБРАЗОВАНИЕ ПУТЕЙ В ОТНОСИТЕЛЬНЫЕ
    # print(f"\n🔄 Преобразование путей в относительные...")
    # scan_dirs_data = convert_to_relative_paths(
    #     scan_dirs_data, 
    #     config_data['output_path']
    # )
    
    # Проверка после преобразования
    print(f"   • Пример относительного пути: {scan_dirs_data[0][2]}")
    
    # Проверяем, что есть что индексировать
    if not scan_dirs_data:
        print("\n❌ Ошибка: Не удалось просканировать ни один каталог")
        print("   Проверьте пути в config.ini")
        return 1
    
    if not file_index_data:
        print("\n⚠️  Предупреждение: Не найдено файлов для индексации")
        print("   Проверьте расширения файлов в config.ini")
    
    # ПРОВЕРКА ПУТЕЙ (добавьте этот блок для отладки)
    print(f"\n🔍 Проверка структуры данных:")
    print(f"   • Каталогов: {len(scan_dirs_data)}")
    print(f"   • Файлов: {len(file_index_data)}")
    if file_index_data and len(file_index_data) > 0:
        print(f"   • Примеры путей в fileIndex:")
        for i in range(min(3, len(file_index_data))):
            file = file_index_data[i]
            dir_id, file_path = file
            dir_name = scan_dirs_data[dir_id][1]
            print(f"     - [{dir_id}] {dir_name}: {file_path}")
    # Конец блока проверки
    
    # Генерируем HTML страницу
    print(f"\n🎨 Подготовка к генерации HTML...")
    print(f"   • Шаблон: template.html")
    print(f"   • Стили: styles.css")
    print(f"   • JavaScript: search.js")
    print(f"   • Данные: {len(file_index_data)} файлов, {len(scan_dirs_data)} каталогов")
    
    success = generate_html_page(
        config_data['output_path'],
        scan_dirs_data,
        file_index_data,
        stats,
        config_data,
        'template.html',
        'styles.css',
        'search.js'
    )
    
    if success:
        print(f"\n✅ HTML страница успешно создана!")
        print(f"   • Файл: {config_data['output_path']}")
        print(f"   • Файлов в индексе: {stats['total_files']}")
        print(f"   • Каталогов: {stats['total_directories']}")
        
        # Проверяем размер файла
        if os.path.exists(config_data['output_path']):
            file_size = os.path.getsize(config_data['output_path'])
            print(f"   • Размер файла: {file_size / 1024:.1f} KB")
            print(f"\n🎉 Готово! Откройте файл в браузере для проверки.")
        else:
            print(f"⚠️  Внимание: Файл не найден по указанному пути")
        
        return 0
    else:
        print("\n❌ Ошибка при создании HTML страницы")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)