from fpdf import FPDF

SCREENSHOT_MAIN = "C:\\Users\\user\\Documents\\New OpenCode Project\\dist\\screenshot_main.png"
SCREENSHOT_MARKERS = "C:\\Users\\user\\Documents\\New OpenCode Project\\dist\\screenshot_markers.png"

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_font("Segoe", "", "C:\\Windows\\Fonts\\segoeui.ttf")
pdf.add_font("Segoe", "B", "C:\\Windows\\Fonts\\segoeuib.ttf")

# ============== COVER ==============
pdf.add_page()
pdf.ln(50)
pdf.set_font("Segoe", "B", 28)
pdf.cell(0, 15, "IVI Admin Editor", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.ln(4)
pdf.set_font("Segoe", "", 12)
pdf.multi_cell(0, 7, "Утилита для инжеста и тестирования контента IVI\n\n"
                      "Автоматизация разметки видео, генерация меток,\n"
                      "заполнение формы админки IVI\n\n", align="C")
pdf.ln(6)
pdf.set_font("Segoe", "", 10)
pdf.cell(0, 6, "Версия: июль 2026", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.cell(0, 6, "Распространяется с установщиком IVI_Admin_Editor_Setup.exe", new_x="LMARGIN", new_y="NEXT", align="C")

# ============== 1. ОБЗОР ==============
pdf.add_page()
pdf.set_font("Segoe", "B", 16)
pdf.cell(0, 10, "1. Обзор", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"IVI Admin Editor — настольное приложение для Windows, помогающее "
"размечать видео (мидролы, заставки, построл, длительность) и "
"автоматически заполнять поля веб-админки IVI через Chrome-расширение.\n\n"
"Основные возможности:\n"
"- Сервер localhost:8766 для обмена данными с Chrome-расширением\n"
"- Панель меток с таймером, синхронизированным с браузерным плеером\n"
"- Хоткеи 1–7 из браузера (с намлока тоже)\n"
"- Горячая клавиша Ctrl+M для заполнения формы админки\n"
"- Шаблоны меток для повторяющихся заставок\n"
"- Редактирование меток прямо в окне приложения\n"
"- Авто-установка начала заставки в 0 при нажатии «Кон.заст.»\n"
"- Авто-определение длительности из плеера\n"
"- Автоматическое заполнение формы админки IVI\n"
"- Сохранение меток в markers.json при закрытии")
pdf.ln(4)

# ============== 2. ГЛАВНОЕ ОКНО ==============
pdf.add_page()
pdf.set_font("Segoe", "B", 16)
pdf.cell(0, 10, "2. Главное окно", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Главное окно (IVI) содержит сервер и элементы управления:\n\n"
"1. Статус сервера — «Статус: запущен / остановлен»\n"
"2. URL сервера — http://localhost:8766\n"
"3. Лог событий — список всех действий\n"
"4. «Остановить сервер» — завершает работу\n"
"5. «Открыть в браузере» — открывает http://localhost:8766\n"
"6. «Отчет» — открывает report.txt\n"
"7. «Метки» — открывает панель разметки\n\n"
"Сервер запускается автоматически. Через 3 сек открывается report.txt.")
pdf.ln(4)

if pdf.page_no() > 1:
    pdf.image(SCREENSHOT_MAIN, x=20, w=170)
    pdf.ln(5)

# ============== 3. ПАНЕЛЬ МЕТОК ==============
pdf.add_page()
pdf.set_font("Segoe", "B", 16)
pdf.cell(0, 10, "3. Панель меток (MarkersPanel)", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Открывается кнопкой «Метки» из главного окна. Окно 480x720.\n\n"
"Таймер (вверху): время в формате ЧЧ:ММ:СС. Синхронизируется с браузерным плеером: "
"play/pause/seek в браузере обновляет таймер.\n\n"
"Кнопки управления:\n"
"- Пауза — запустить/остановить таймер вручную\n"
"- Сброс — сбросить таймер в 00:00:00\n"
"- Отм. — отменить последнюю добавленную метку\n"
"- Очистить — удалить ВСЕ метки")
pdf.ln(4)

pdf.image(SCREENSHOT_MARKERS, x=40, w=130)
pdf.ln(95)

pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Цветные кнопки меток (с номерами хоткеев):\n"
"1 — «Мидрол» (синий) — текущее время в список midroll\n"
"2 — «Нач.заст.» (зелёный) — начало заставки\n"
"3 — «Кон.заст.» (зелёный) — конец заставки\n"
"    (если начало не отмечено, ставится 00:00:00 авто)\n"
"4 — «Нач.пред.» (фиолетовый) — начало предыдущей\n"
"5 — «Кон.пред.» (фиолетовый) — конец предыдущей\n"
"6 — «Построл» (оранжевый) — время титров\n"
"7 — «Длит.» (красный) — общая длительность видео\n"
"    (автоматически определяется из плеера при первом воспроизведении)")

# ============== 4. ХОТКЕИ ИЗ БРАУЗЕРА ==============
pdf.add_page()
pdf.set_font("Segoe", "B", 16)
pdf.cell(0, 10, "4. Хоткеи из браузера", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Chrome-расширение перехватывает нажатия клавиш на странице с видео "
"(кроме полей ввода) и отправляет команду на сервер.\n\n"
"Цифровые хоткеи (работают и на основном блоке, и на намлоке):\n"
"  1 → Мидрол        5 → Кон.пред.\n"
"  2 → Нач.заст.     6 → Построл\n"
"  3 → Кон.заст.     7 → Длит.\n"
"  4 → Нач.пред.\n\n"
"Ctrl+M → нажать кнопку «Заполнить из IVI» на странице админки\n\n"
"Время берётся с video-элемента на странице. Сервер прокручивает "
"таймер на нужную секунду и выполняет действие.")
pdf.ln(4)

# ============== 5. РЕДАКТИРОВАНИЕ И ШАБЛОНЫ ==============
pdf.add_page()
pdf.set_font("Segoe", "B", 16)
pdf.cell(0, 10, "5. Редактирование меток и шаблоны", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Segoe", "", 10)

pdf.set_font("Segoe", "B", 12)
pdf.cell(0, 8, "Редактирование меток", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Под цветными кнопками — сводка меток. Каждое значение отображается "
"в поле ввода с форматом ЧЧ:ММ:СС.\n"
"Если промахнулись при нажатии:\n"
"1. Кликните в поле нужной метки\n"
"2. Исправьте время\n"
"3. Enter или клик в другое место — метка обновится\n\n"
"Форматы ввода: ЧЧ:ММ:СС, ММ:СС или просто секунды.")
pdf.ln(4)

pdf.set_font("Segoe", "B", 12)
pdf.cell(0, 8, "Шаблоны меток", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Если заставки (и другие метки) одинаковые во всех видео:\n\n"
"1. Разметьте одно видео, нажмите «Запомнить шаблон»\n"
"   — все текущие метки сохраняются в markers_template.json\n"
"2. Для следующего видео нажмите «Вставить шаблон»\n"
"   — все метки применяются к текущему ролику\n\n"
"Шаблон сохраняется между сеансами (на диске).\n"
"При вставке мидролы не затрагиваются — применяются только заставки, "
"предыдущие, построл и длительность.")
pdf.ln(4)

pdf.set_font("Segoe", "B", 12)
pdf.cell(0, 8, "Авто-начало заставки", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Если нажать «Кон.заст.», а начало заставки ещё не отмечено, "
"оно автоматически ставится на 00:00:00.")

# ============== 6. CHROME-РАСШИРЕНИЕ ==============
pdf.add_page()
pdf.set_font("Segoe", "B", 16)
pdf.cell(0, 10, "6. Chrome-расширение", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Segoe", "", 10)

pdf.multi_cell(0, 5,
"Расширение «IVI Fill» (manifest v3) — папка ivi_ext/.\n\n"
"Кнопка «Заполнить из IVI»:\n"
"- Появляется в правом верхнем углу страницы админки\n"
"- При нажатии (или Ctrl+M) отправляет fetch на localhost:8766\n"
"- Заполняет поля:\n"
"  midrolls → id_middroll-*-time\n"
"  start_scale / finish_scale → localization_labels-0\n"
"  start_prev / finish_prev → localization_labels-1\n"
"  postroll → id_credits_begin_time\n"
"  duration → id_duration и localizations-*-duration\n"
"- Автоматически добавляет строки формсетов\n"
"- Показывает alert «Готово! Форма заполнена.»")
pdf.ln(4)

pdf.set_font("Segoe", "B", 12)
pdf.cell(0, 8, "Синхронизация плеера", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Расширение находит все video-элементы и отслеживает:\n"
"- play / pause / seeked — отправляет команду на сервер\n"
"- timeupdate — каждую секунду шлёт текущее время\n"
"- loadedmetadata — отправляет общую длительность видео\n"
"Сервер обновляет таймер в панели меток. Длительность проставляется "
"автоматически при первом воспроизведении.")

pdf.set_font("Segoe", "B", 12)
pdf.cell(0, 8, "Хоткеи", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Расширение слушает keydown на всей странице:\n"
"- Цифры 1–7 (и numpad 1–7) → маркеры\n"
"- Ctrl+M → заполнить форму админки\n"
"Не срабатывает внутри полей ввода.")

# ============== 7. ТЕХНИЧЕСКИЕ ДЕТАЛИ ==============
pdf.add_page()
pdf.set_font("Segoe", "B", 16)
pdf.cell(0, 10, "7. Технические детали", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"HTTP-сервер:\n"
"- Порт: 8766, хост: localhost\n"
"- Endpoints:\n"
"    GET / — метки + пустые поля (JSON)\n"
"    GET /markers — только метки (JSON)\n"
"    GET /sync?state=pause|play|seek&time=N&duration=N — синхронизация плеера\n"
"    GET /sync?key=midroll&time=N — хоткей из браузера\n\n"
"Файлы данных:\n"
"- markers.json — сохранение меток при закрытии панели\n"
"- markers_template.json — шаблон меток\n"
"- report.txt — текстовый отчёт\n\n"
"Поток данных хоткеев:\n"
"1. keydown в браузере → fetch /sync?key=...&time=...\n"
"2. _poll_sync (каждые 200 мс) → panel.elapsed = time\n"
"3. → panel.mark_xxx() (та же функция, что при нажатии кнопки)\n\n"
"Поток данных синхронизации:\n"
"1. Браузер → /sync → _sync_state (dict)\n"
"2. _poll_sync → video_play/pause/seek\n\n"
"Примечания:\n"
"- Окно меток всегда поверх всех окон (topmost)\n"
"- Хоткеи только из браузера (не из окна программы)")

# ============== 8. УСТАНОВКА ==============
pdf.add_page()
pdf.set_font("Segoe", "B", 16)
pdf.cell(0, 10, "8. Установка", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Segoe", "", 10)
pdf.multi_cell(0, 5,
"Установка на целевой ноутбук:\n\n"
"1. Запустите IVI_Admin_Editor_Setup.exe от имени администратора\n"
"2. Установщик создаст:\n"
"   - C:\\Program Files\\IVI Admin Editor\\ivi_meta.exe\n"
"   - Папку с расширением для Chrome в C:\\Program Files\\IVI Admin Editor\\ivi_ext\\\n"
"   - Ярлык «IVI Admin Editor» на рабочем столе (опционально)\n"
"   - Ярлык «IVI Admin Editor (Chrome)» для запуска с расширением (опционально)\n"
"3. После установки программа запустится автоматически (если отмечено)\n\n"
"Установка Chrome-расширения (вручную):\n"
"1. Открыть chrome://extensions/\n"
"2. Включить «Режим разработчика»\n"
"3. Нажать «Загрузить распакованное расширение»\n"
"4. Выбрать папку C:\\Program Files\\IVI Admin Editor\\ivi_ext\\\n\n"
"Либо в установщике отметить «Установить расширение для Chrome и Яндекс.Браузер» — "
"будет создан ярлык для запуска браузера с расширением.\n\n"
"Установка из исходников:\n"
"  pip install pyinstaller\n"
"  pyinstaller ivi_meta.spec --clean --noconfirm\n"
"  iscc installer.iss")

pdf.output("C:\\Users\\user\\AppData\\Local\\Temp\\IVI Admin Editor.pdf")
print("PDF created")
