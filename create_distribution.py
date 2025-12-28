"""
Утилита создания дистрибутива для системы Poisk
Репозиторий: https://github.com/prog815/poisk
Версия: 1.0.3

Создает архив с файлами .txt для публикации на GitHub.
"""

import os
import sys
import zipfile
import shutil
from datetime import datetime

def create_distribution():
    """
    Создает дистрибутив системы Poisk
    """
    print("=" * 60)
    print("Poisk - Создание дистрибутива")
    print("=" * 60)
    print()
    
    # Файлы для включения в дистрибутив
    files_to_package = [
        "generate_search_page.py",
        "template.html", 
        "styles.css",
        "search.js",
        "README.md"  # Добавляем README.md
    ]
    
    # Проверяем наличие всех файлов
    print("📋 Проверка файлов для дистрибутива...")
    missing_files = []
    
    for filename in files_to_package:
        if os.path.exists(filename):
            print(f"   ✓ {filename}")
        else:
            print(f"   ✗ {filename} (не найден)")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n❌ Ошибка: Не найдены файлы: {', '.join(missing_files)}")
        print("   Создайте недостающие файлы перед созданием дистрибутива.")
        return False
    
    # Создаем временную папку для дистрибутива
    dist_dir = "dist_temp"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    
    os.makedirs(dist_dir, exist_ok=True)
    
    # Копируем файлы с добавлением .txt расширения
    print(f"\n📦 Подготовка файлов...")
    
    # 1. Копируем основные файлы
    for filename in files_to_package:
        source_path = filename
        dest_filename = f"{filename}.txt"
        dest_path = os.path.join(dist_dir, dest_filename)
        
        try:
            with open(source_path, 'r', encoding='utf-8') as src_file:
                content = src_file.read()
            
            with open(dest_path, 'w', encoding='utf-8') as dst_file:
                dst_file.write(content)
            
            print(f"   ✓ {filename} → {dest_filename}")
            
        except Exception as e:
            print(f"   ✗ Ошибка обработки {filename}: {e}")
            return False
    
    # 2. Создаем config.ini.template из config.ini или создаем новый
    print(f"\n⚙️  Создание шаблона конфигурации...")
    config_template_path = os.path.join(dist_dir, "config.ini.template.txt")
    
    if os.path.exists("config.ini"):
        try:
            with open("config.ini", 'r', encoding='utf-8') as src_file:
                config_content = src_file.read()
            
            # Делаем его более понятным как шаблон
            template_content = config_content.replace(
                "scan_directories = ", 
                "# Пример: \\\\server\\share\\docs:Документы, /mnt/share/projects:Проекты\nscan_directories = "
            ).replace(
                "output_path = ", 
                "# Пример: \\\\server\\share\\search.html или /mnt/share/search.html\noutput_path = "
            )
            
            with open(config_template_path, 'w', encoding='utf-8') as dst_file:
                dst_file.write(template_content)
            
            print(f"   ✓ Создан config.ini.template.txt из config.ini")
            
        except Exception as e:
            print(f"   ✗ Ошибка создания шаблона: {e}")
            create_default_config_template(config_template_path)
    else:
        create_default_config_template(config_template_path)
    
    # Создаем архив
    print(f"\n🗜️  Создание архива...")
    version = get_version_from_files()
    archive_name = f"poisk_distribution.zip"
    
    try:
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Добавляем файлы из временной папки
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dist_dir)
                    zipf.write(file_path, arcname)
        
        # Проверяем размер архива
        archive_size = os.path.getsize(archive_name) / 1024 / 1024
        
        print(f"   ✓ Архив создан: {archive_name}")
        print(f"   📊 Размер архива: {archive_size:.2f} MB")
        
    except Exception as e:
        print(f"   ✗ Ошибка создания архива: {e}")
        return False
    
    # Очищаем временную папку
    shutil.rmtree(dist_dir)
    
    print(f"\n✅ Дистрибутив успешно создан!")
    print(f"   📦 Файл: {archive_name}")
    print(f"   🏷️  Версия: {version}")
    print(f"   📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    print("📋 Содержимое дистрибутива (все файлы с расширением .txt):")
    for filename in files_to_package:
        print(f"   • {filename}.txt")
    print("   • config.ini.template.txt")
    print()
    print("📝 Действия для публикации (выполнить вручную):")
    print(f"   1. ЗАГРУЗИТЬ файл '{archive_name}' в репозиторий GitHub")
    print("   2. УБЕДИТЕСЬ что ссылка в README.md.txt указывает на этот файл:")
    print(f"      - Название дистрибутива: '{archive_name}'")
    print(f"      - Версия: v{version}")
    print("   3. СОЗДАТЬ новый релиз на GitHub (Releases)")
    print(f"      - Название: Poisk v{version}")
    print(f"      - Прикрепить файл: {archive_name}")
    print("      - Добавить описание изменений")
    print()
    print("⚠️  Важно: Все файлы в архиве имеют расширение .txt")
    print("   Администратор должен переименовать их при установке.")
    
    return True

def create_default_config_template(filepath):
    """
    Создает шаблон конфигурационного файла
    """
    template_content = """; ============================================
; ШАБЛОН конфигурации системы Poisk
; Скопируйте этот файл в config.ini и настройте
; ============================================

[PATHS]
# Каталоги для сканирования (полный_путь:КороткоеИмя)
scan_directories = 

# Путь для сохранения страницы поиска
output_path = 

# ПОЛНЫЙ путь к файлу меню (если есть, опционально)
menu_file_path = 

[SETTINGS]
max_files = 200000
results_per_page = 10
file_extensions = pdf,doc,docx,xls,xlsx,ppt,pptx,txt,py,js,html,css,java,cpp,h,zip,rar,7z
config_version = 1.0
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"   ✓ Создан стандартный config.ini.template.txt")

def get_version_from_files():
    """
    Извлекает версию из файлов проекта
    """
    version = "1.0.0"
    
    try:
        with open('generate_search_page.py', 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            for line in lines:
                if 'Версия:' in line:
                    parts = line.split('Версия:')
                    if len(parts) > 1:
                        version_candidate = parts[1].strip().strip("'\"")
                        if version_candidate:
                            version = version_candidate
                            break
    except:
        pass
    
    return version

def main():
    """
    Основная функция
    """
    try:
        success = create_distribution()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()