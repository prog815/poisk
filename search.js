/**
 * Корпоративный поисковик для локальной сети
 * JavaScript логика поиска
 * Версия: 1.0.0
 */

// ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
let currentSearchResults = [];
let currentDisplayIndex = 0;
let currentSearchQuery = '';
let resultsPerPage = 10;

// ===== ОСНОВНЫЕ ФУНКЦИИ ПОИСКА =====

/**
 * Подготавливает поисковый запрос
 * @param {string} userInput - Введенный пользователем текст
 * @returns {Object} Объект с оригинальным и очищенным запросом
 */
function prepareSearchQuery(userInput) {
    // Сохраняем оригинал для отображения
    const displayQuery = userInput;
    
    // Очищаем для поиска (удаляем все кроме букв, цифр, пробелов)
    let searchQuery = userInput.toLowerCase()
        .replace(/[^а-яёa-z0-9\s]/gi, ' ')  // Удаляем спецсимволы
        .replace(/\s+/g, ' ')              // Множественные пробелы → один
        .trim();
    
    return {
        display: displayQuery,  // Оригинальный запрос
        search: searchQuery     // Запрос в нижнем регистре для поиска
    };
}

/**
 * Ищет файлы в индексе по запросу
 * @param {Object} queryObj - Объект с очищенным запросом
 * @returns {Array} Массив найденных файлов
 */
function searchInIndex(queryObj) {
    // Если пустой запрос - возвращаем пустой массив
    if (!queryObj.search) {
        return [];
    }
    
    const words = queryObj.search.split(/\s+/);
    const results = [];
    
    // Проходим по всему индексу файлов
    for (let i = 0; i < window.fileIndex.length; i++) {
        const file = window.fileIndex[i];
        const dirId = file[0];
        const filePath = file[1]; // ОРИГИНАЛЬНЫЙ путь
        
        // Для поиска приводим к нижнему регистру
        const filePathLower = filePath.toLowerCase();
        
        // Проверяем, содержит ли путь ВСЕ слова запроса
        let matchesAll = true;
        for (let j = 0; j < words.length; j++) {
            if (filePathLower.indexOf(words[j]) === -1) {
                matchesAll = false;
                break;
            }
        }
        
        if (matchesAll) {
            // Добавляем информацию о каталоге
            const dirInfo = window.scanDirs[dirId];
            results.push({
                dirId: dirId,
                dirName: dirInfo[1],
                dirPath: dirInfo[2],
                filePath: filePath, // Оригинальный путь
                originalPath: file[1]
            });
        }
    }
    
    return results;
}

/**
 * Разделяет полный путь на путь и имя файла
 * @param {string} fullPath - Полный путь к файлу
 * @returns {Object} Объект с путем и именем файла
 */
function splitPathAndFilename(fullPath) {
    // Если файл в корне каталога сканирования (нет слешей)
    if (fullPath.indexOf('\\') === -1 && fullPath.indexOf('/') === -1) {
        return {path: '', filename: fullPath};
    }
    
    // Находим последний разделитель
    const lastSlash = Math.max(fullPath.lastIndexOf('\\'), fullPath.lastIndexOf('/'));
    
    return {
        path: fullPath.substring(0, lastSlash),
        filename: fullPath.substring(lastSlash + 1)
    };
}

/**
 * Подсвечивает найденные слова в тексте
 * @param {string} text - Исходный текст
 * @param {Array} searchWords - Массив слов для подсветки
 * @returns {string} Текст с HTML разметкой для подсветки
 */
function highlightSearchWords(text, searchWords) {
    if (!text || !searchWords || searchWords.length === 0) {
        return escapeHtml(text);
    }
    
    let highlightedText = escapeHtml(text);
    
    // Для каждого слова поиска
    searchWords.forEach(word => {
        if (word.length < 2) return;
        
        // Создаем регулярное выражение без учета регистра
        const regex = new RegExp(`(${escapeRegExp(word)})`, 'gi');
        highlightedText = highlightedText.replace(
            regex, 
            '<mark class="search-highlight">$1</mark>'
        );
    });
    
    return highlightedText;
}

/**
 * Экранирует специальные символы для регулярных выражений
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Создает HTML для отображения файла
 * @param {Object} fileData - Данные файла
 * @param {Array} searchWords - Массив слов поискового запроса
 * @returns {string} HTML строка
 */
function createFileResultHTML(fileData, searchWords = []) {
    const pathParts = splitPathAndFilename(fileData.filePath); // Оригинальный путь
    const dirInfo = window.scanDirs[fileData.dirId];
    
    if (!dirInfo) return `<div class="result-card">Ошибка каталога</div>`;
    
    const dirName = dirInfo[1]; // Короткое имя
    const dirPath = dirInfo[2]; // Полный путь
    
    // Получаем базовое имя каталога (сохраняем оригинальный регистр)
    let baseFolderName;
    if (dirPath.includes('\\')) {
        const parts = dirPath.split('\\').filter(Boolean);
        baseFolderName = parts[parts.length - 1]; // Последняя часть с оригинальным регистром
    } else {
        const parts = dirPath.split('/').filter(Boolean);
        baseFolderName = parts[parts.length - 1];
    }
    
    // Формируем пути с сохранением оригинального регистра
    const relativeFilePath = baseFolderName + '/' + fileData.filePath;
    const relativeFolderPath = pathParts.path ? 
        baseFolderName + '/' + pathParts.path : 
        baseFolderName;
    
    // Подсвечиваем слова (сохраняем оригинальный регистр текста)
    const highlightedPath = highlightSearchWords(pathParts.path, searchWords);
    const highlightedFilename = highlightSearchWords(pathParts.filename, searchWords);
    
    return `
        <div class="result-card">
            <span class="directory-name">${escapeHtml(dirName)}</span>
            <a href="${escapeHtml(relativeFolderPath)}" 
               class="file-path" 
               title="Открыть папку в новой вкладке"
               target="_blank"
               rel="noopener noreferrer">
                ${highlightedPath || '<span class="empty-path">(корень каталога)</span>'}${pathParts.path ? '/' : ''}
            </a>
            <a href="${escapeHtml(relativeFilePath)}" 
               class="file-name" 
               title="Открыть файл в новой вкладке"
               target="_blank"
               rel="noopener noreferrer">
                ${highlightedFilename}
            </a>
        </div>
    `;
}

/**
 * Отображает результаты поиска
 * @param {Array} results - Массив найденных файлов
 * @param {Object} query - Объект запроса
 */
function displaySearchResults(results, query) {
    const resultsContainer = document.getElementById('resultsContainer');
    const noResultsElement = document.getElementById('noResults');
    const showMoreButton = document.getElementById('showMoreButton');
    const searchStatus = document.getElementById('searchStatus');
    const resultsCount = document.getElementById('resultsCount');
    
    // Сохраняем текущие результаты
    currentSearchResults = results;
    currentDisplayIndex = 0;
    currentSearchQuery = query.display;
    
    // Получаем слова для подсветки
    const searchWords = query.search ? query.search.split(/\s+/) : [];
    
    // Обновляем информацию о поиске
    if (query.search) {
        searchStatus.textContent = `Поиск: "${query.display}"`;
        resultsCount.textContent = `Найдено: ${results.length}`;
        resultsCount.classList.add('visible');
    } else {
        searchStatus.textContent = 'Готов к поиску';
        resultsCount.textContent = '';
        resultsCount.classList.remove('visible');
    }
    
    // Очищаем контейнер результатов
    resultsContainer.innerHTML = '';
    
    // Показываем/скрываем сообщение "ничего не найдено"
    if (query.search && results.length === 0) {
        noResultsElement.style.display = 'block';
        showMoreButton.style.display = 'none';
    } else {
        noResultsElement.style.display = 'none';
        
        // Показываем первую страницу результатов
        if (results.length > 0) {
            // Показываем первые resultsPerPage результатов
            const endIndex = Math.min(resultsPerPage, results.length);
            
            for (let i = 0; i < endIndex; i++) {
                const fileData = results[i];
                const fileHTML = createFileResultHTML(fileData, searchWords);
                resultsContainer.insertAdjacentHTML('beforeend', fileHTML);
            }
            
            currentDisplayIndex = endIndex;
            
            // Показываем кнопку "Показать еще" если есть еще результаты
            if (results.length > resultsPerPage) {
                showMoreButton.style.display = 'block';
            } else {
                showMoreButton.style.display = 'none';
            }
        } else {
            // Показываем стартовый экран
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <h3>Начните поиск</h3>
                    <p>Введите запрос в строку поиска выше</p>
                </div>
            `;
            showMoreButton.style.display = 'none';
        }
    }
}

/**
 * Показывает следующую страницу результатов
 */
function showMoreResults() {
    const resultsContainer = document.getElementById('resultsContainer');
    const showMoreButton = document.getElementById('showMoreButton');
    
    // Получаем слова для подсветки из текущего запроса
    const searchWords = currentSearchQuery ? 
        prepareSearchQuery(currentSearchQuery).search.split(/\s+/) : [];
    
    // Определяем сколько результатов показать
    const endIndex = Math.min(
        currentDisplayIndex + resultsPerPage,
        currentSearchResults.length
    );
    
    // Добавляем следующие результаты
    for (let i = currentDisplayIndex; i < endIndex; i++) {
        const fileData = currentSearchResults[i];
        const fileHTML = createFileResultHTML(fileData, searchWords);
        resultsContainer.insertAdjacentHTML('beforeend', fileHTML);
    }
    
    // Обновляем индекс
    currentDisplayIndex = endIndex;
    
    // Скрываем кнопку если показали все результаты
    if (currentDisplayIndex >= currentSearchResults.length) {
        showMoreButton.style.display = 'none';
    }
}

/**
 * Выполняет поиск по введенному запросу
 */
function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = prepareSearchQuery(searchInput.value);
    
    // Выполняем поиск
    const results = searchInIndex(query);
    
    // Отображаем результаты
    displaySearchResults(results, query);
}

/**
 * Открывает папку с файлом
 * @param {string} dirId - ID каталога
 * @param {string} relativePath - Относительный путь к папке
 */
function openFolder(dirId, relativePath) {
    const dirInfo = window.scanDirs[dirId];
    if (!dirInfo) return;
    
    const dirPath = dirInfo[2]; // Полный путь к каталогу сканирования
    
    // Строим полный путь
    let fullPath;
    if (relativePath) {
        fullPath = dirPath + '/' + relativePath;
    } else {
        fullPath = dirPath;
    }
    
    // Нормализуем путь для file:// URL
    fullPath = normalizePathForFileURL(fullPath);
    
    console.log('Открытие папки:', fullPath);
    
    // Показываем путь и даем возможность скопировать
    alert(`Путь к папке:\n${fullPath}\n\nСкопируйте этот путь в проводник.`);
    
    // Пытаемся открыть через file:// (работает не во всех браузерах)
    try {
        window.open(`file:///${fullPath}`);
    } catch (error) {
        console.log('Браузер не разрешил открыть file:// URL');
    }
}

/**
 * Открывает файл
 * @param {string} dirId - ID каталога
 * @param {string} relativePath - Относительный путь к файлу
 */
function openFile(dirId, relativePath) {
    const dirInfo = window.scanDirs[dirId];
    if (!dirInfo) return;
    
    const dirPath = dirInfo[2]; // Полный путь к каталогу сканирования
    const fullPath = dirPath + '/' + relativePath;
    const normalizedPath = normalizePathForFileURL(fullPath);
    
    console.log('Открытие файла:', normalizedPath);
    
    // Показываем путь и даем возможность скопировать
    alert(`Путь к файлу:\n${normalizedPath}\n\nСкопируйте этот путь.`);
    
    // Пытаемся открыть через file:// (работает не во всех браузерах)
    try {
        window.open(`file:///${normalizedPath}`);
    } catch (error) {
        console.log('Браузер не разрешил открыть file:// URL');
    }
}

/**
 * Нормализует путь для использования в file:// URL
 * @param {string} path - Исходный путь
 * @returns {string} Нормализованный путь
 */
function normalizePathForFileURL(path) {
    // Сохраняем оригинальный путь
    let normalized = path;
    
    // Заменяем обратные слеши на прямые
    normalized = normalized.replace(/\\/g, '/');
    
    // Убираем лишние слеши
    normalized = normalized.replace(/\/+/g, '/');
    
    // Кодируем спецсимволы для URL (пробелы, скобки и т.д.)
    // Разбиваем на части и кодируем каждую часть
    const parts = normalized.split('/');
    const encodedParts = parts.map(part => encodeURIComponent(part));
    normalized = encodedParts.join('/');
    
    return normalized;
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

/**
 * Экранирует HTML спецсимволы
 * @param {string} text - Текст для экранирования
 * @returns {string} Экранированный текст
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Экранирует строку для использования в JavaScript
 * @param {string} text - Текст для экранирования
 * @returns {string} Экранированный текст
 */
function escapeJs(text) {
    return String(text || '')
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r');
}

/**
 * Отображает информацию о базе данных
 */
function displayDatabaseInfo() {
    const databaseStats = document.getElementById('databaseStats');
    const systemVersion = document.getElementById('systemVersion');
    const supportedExtensions = document.getElementById('supportedExtensions');
    
    if (!window.systemInfo) return;
    
    // Версия системы только в подвале
    if (systemVersion) {
        systemVersion.textContent = window.systemInfo.version || '1.0.0';
    }
    
    // Информация о базе (4 пункта, без версии)
    if (databaseStats) {
        databaseStats.innerHTML = `
            <li>Дата последнего обновления: ${escapeHtml(window.systemInfo.lastUpdated)}</li>
            <li>Всего файлов в индексе: ${window.systemInfo.totalFiles.toLocaleString()}</li>
            <li>Каталогов сканирования: ${window.systemInfo.directories}</li>
            <li>Типы файлов: ${escapeHtml(window.systemInfo.extensions.join(', '))}</li>
        `;
    }
    
    // Скрываем блок с расширениями в справке если он есть
    if (supportedExtensions) {
        supportedExtensions.style.display = 'none';
        const extensionsTitle = supportedExtensions.previousElementSibling;
        if (extensionsTitle && extensionsTitle.tagName === 'H3' && 
            extensionsTitle.textContent.includes('Поддерживаемые типы')) {
            extensionsTitle.style.display = 'none';
        }
    }
}

/**
 * Отображает информацию о каталогах сканирования
 */
function displayDirectoriesInfo() {
    const directoriesInfo = document.getElementById('directoriesInfo');
    
    if (!window.scanDirs || !directoriesInfo) return;
    
    directoriesInfo.innerHTML = window.scanDirs
        .map(dir => `<span>${escapeHtml(dir[1])}</span>`)
        .join('');
}

/**
 * Инициализирует выпадающую справку
 */
function initHelpDropdown() {
    const helpToggle = document.getElementById('helpToggle');
    const helpContent = document.getElementById('helpContent');
    
    if (!helpToggle || !helpContent) return;
    
    helpToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        helpContent.style.display = helpContent.style.display === 'block' ? 'none' : 'block';
    });
    
    // Закрываем справку при клике вне ее
    document.addEventListener('click', function() {
        helpContent.style.display = 'none';
    });
    
    // Предотвращаем закрытие при клике внутри справки
    helpContent.addEventListener('click', function(e) {
        e.stopPropagation();
    });
}

// ===== ОБРАБОТЧИКИ СОБЫТИЙ =====

/**
 * Инициализирует обработчики событий
 */
function initEventHandlers() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const showMoreButton = document.getElementById('showMoreButton');
    
    // Поиск по кнопке
    if (searchButton) {
        searchButton.addEventListener('click', performSearch);
    }
    
    // Поиск по Enter
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // Очистка результатов при очистке поля
        searchInput.addEventListener('input', function() {
            if (this.value === '') {
                displaySearchResults([], {display: '', search: ''});
            }
        });
    }
    
    // Кнопка "Показать еще"
    if (showMoreButton) {
        showMoreButton.addEventListener('click', showMoreResults);
    }
    
    // Устанавливаем количество результатов на страницу
    if (window.systemInfo && window.systemInfo.resultsPerPage) {
        resultsPerPage = window.systemInfo.resultsPerPage;
        const resultsPerPageElement = document.getElementById('resultsPerPage');
        if (resultsPerPageElement) {
            resultsPerPageElement.textContent = resultsPerPage;
        }
    }
}

// ===== ИНИЦИАЛИЗАЦИЯ =====

/**
 * Инициализирует приложение при загрузке страницы
 */
function initApp() {
    console.log('Инициализация поисковика...');
    
    // Проверяем наличие необходимых данных
    if (!window.fileIndex || !window.scanDirs || !window.systemInfo) {
        console.error('Отсутствуют необходимые данные для поиска');
        return;
    }
    
    console.log(`Загружено файлов: ${window.fileIndex.length}`);
    console.log(`Каталогов: ${window.scanDirs.length}`);
    
    // Инициализируем компоненты
    displayDatabaseInfo();
    displayDirectoriesInfo();
    initHelpDropdown();
    initEventHandlers();
    
    // Устанавливаем фокус на поле поиска
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.focus();
    }
    
    console.log('Поисковик готов к работе');
}

// Запускаем инициализацию при загрузке страницы
document.addEventListener('DOMContentLoaded', initApp);