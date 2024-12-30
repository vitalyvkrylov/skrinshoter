import pyautogui  # Импортируем библиотеку для создания скриншотов
import tkinter as tk  # Импортируем библиотеку для создания графического интерфейса
from tkinter import messagebox  # Импортируем модуль для отображения всплывающих сообщений
from datetime import datetime  # Импортируем модуль для работы с датой и временем
import os  # Импортируем библиотеку для работы с файловой системой
from pystray import Icon, MenuItem, Menu  # Импортируем модули для работы с иконкой в системном трее
from PIL import Image, ImageDraw  # Импортируем библиотеки PIL для работы с изображениями и рисования
import threading  # Импортируем библиотеку для многозадачности
from tkinter import filedialog  # Импортируем диалог выбора файлов и папок
from tkinter import ttk

import sqlite3

# Настройки программы: путь для сохранения скриншотов в папку img текущего проекта
PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))  # Получаем путь к текущей папке проекта
SAVE_FOLDER = os.path.join(PROJECT_FOLDER, "img")  # Создаём путь к папке img в проекте
# Функция для создания базы данных и таблицы настроек
def update_db_structure():
    conn = sqlite3.connect(os.path.join(PROJECT_FOLDER, 'settings.db'))
    cursor = conn.cursor()

    # Проверяем, есть ли колонка save_folder, если нет - добавляем
    cursor.execute("PRAGMA table_info(settings);")
    columns = cursor.fetchall()
    columns = [column[1] for column in columns]

    if 'save_folder' not in columns:
        cursor.execute("ALTER TABLE settings ADD COLUMN save_folder TEXT;")
    if 'file_format' not in columns:
        cursor.execute("ALTER TABLE settings ADD COLUMN file_format TEXT;")

    conn.commit()
    conn.close()
def create_settings_db():
    conn = sqlite3.connect(os.path.join(PROJECT_FOLDER, 'settings.db'))
    cursor = conn.cursor()

    # Создаём таблицу, если она не существует
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        save_folder TEXT,
                        file_format TEXT)''')

    # Проверим, есть ли уже данные в базе, если нет, добавим стандартные значения
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (save_folder, file_format) VALUES (?, ?)",
                       (SAVE_FOLDER, 'png'))

    conn.commit()
    conn.close()

    # Обновляем структуру базы данных (если необходимо)
    update_db_structure()  # Обновляем структуру таблицы, если нужно

# Функция для получения текущих настроек
def get_settings():
    conn = sqlite3.connect(os.path.join(PROJECT_FOLDER, 'settings.db'))
    cursor = conn.cursor()
    cursor.execute("SELECT save_folder, file_format FROM settings ORDER BY id DESC LIMIT 1")
    settings = cursor.fetchone()
    conn.close()
    return settings if settings else (SAVE_FOLDER, 'png')

# Функция для обновления настроек
def update_settings(save_folder, file_format):
    conn = sqlite3.connect(os.path.join(PROJECT_FOLDER, 'settings.db'))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO settings (save_folder, file_format) VALUES (?, ?)",
                   (save_folder, file_format))
    conn.commit()
    conn.close()
def ensure_save_folder():
    """Проверяет существование папки сохранения, если нет — создаёт её."""
    if not os.path.exists(SAVE_FOLDER):  # Если папка не существует
        os.makedirs(SAVE_FOLDER)  # Создаём папку

# Переменные для координат выделенной области
start_x, start_y, end_x, end_y = 0, 0, 0, 0  # Инициализация переменных для хранения координат начальной и конечной точек
rect_id = None  # Переменная для хранения ID прямоугольника, который будет рисоваться на экране

def start_selection(event):
    """Начало выделения области."""
    global start_x, start_y, rect_id  # Делаем переменные глобальными для использования внутри функции
    start_x, start_y = event.x, event.y  # Сохраняем начальные координаты, где пользователь нажал мышью
    canvas.delete("all")  # Удаляем все старые выделения с экрана
    # Создаём новый прямоугольник, который будет отображать выделенную область
    rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="white", fill="", width=2, dash=(4, 4))

def update_selection(event):
    """Обновление рамки области."""
    global rect_id  # Делаем переменную глобальной для использования внутри функции
    canvas.coords(rect_id, start_x, start_y, event.x, event.y)  # Обновляем координаты прямоугольника в реальном времени

def stop_selection(event):
    """Завершение выделения области и создание скриншота."""
    global end_x, end_y  # Делаем переменные глобальными для использования внутри функции
    end_x, end_y = event.x, event.y  # Сохраняем конечные координаты, когда пользователь отпустил кнопку мыши

    # Вычисляем координаты области, которая была выделена (x1, y1) - начальная точка, (x2, y2) - конечная точка
    x1, y1 = min(start_x, end_x), min(start_y, end_y)
    x2, y2 = max(start_x, end_x), max(start_y, end_y)
    width, height = x2 - x1, y2 - y1  # Рассчитываем ширину и высоту выделенной области

    # Если ширина и высота области больше 0, то делаем скриншот
    if width > 0 and height > 0:
        take_screenshot((x1, y1, width, height))  # Передаем координаты выделенной области в функцию скриншота
    else:
        messagebox.showerror("Ошибка", "Некорректная область для скриншота.")  # Если выделена некорректная область

    # Закрытие окна выделения
    selection_window.destroy()  # Закрываем окно выделения

def select_area():
    """Создает окно для выбора области экрана."""
    global canvas, rect_id, selection_window  # Делаем переменные глобальными

    # Создаем прозрачное окно для выделения области
    selection_window = tk.Toplevel()  # Создаем новое окно
    selection_window.attributes("-fullscreen", True)  # Делаем окно полноэкранным
    selection_window.attributes("-alpha", 0.4)  # Устанавливаем прозрачность окна
    selection_window.config(bg="gray")  # Устанавливаем серый фон

    # Создаем Canvas для отображения рамки выделения
    canvas = tk.Canvas(selection_window, cursor="cross", bg="gray", highlightthickness=0)  # Создаём холст
    canvas.pack(fill=tk.BOTH, expand=True)  # Заполняем всё пространство окна холстом

    # Захватываем события мыши для выделения области
    canvas.bind("<Button-1>", start_selection)  # Когда нажата кнопка мыши, начинается выделение
    canvas.bind("<B1-Motion>", update_selection)  # Когда пользователь двигает мышь, обновляется рамка
    canvas.bind("<ButtonRelease-1>", stop_selection)  # Когда кнопка мыши отпущена, выделение завершено

    root.wait_window(selection_window)  # Ожидаем завершения выделения, чтобы продолжить работу программы
def take_screenshot(region=None):
    """Сделать скриншот области или всего экрана."""
    save_folder, file_format = get_settings()  # Получаем текущие настройки из базы данных
    ensure_save_folder()  # Проверяем, существует ли папка для сохранения, и создаём её, если нет

    try:
        if region:
            screenshot = pyautogui.screenshot(region=region)  # Делаем скриншот выделенной области
        else:
            screenshot = pyautogui.screenshot()  # Если область не задана, делаем скриншот всего экрана

        # Генерируем имя для сохранённого файла с учетом выбранного формата
        filename = os.path.join(save_folder, f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_format}")
        screenshot.save(filename)  # Сохраняем скриншот в файл
        #messagebox.showinfo("Успех", f"Скриншот сохранён: {filename}")  # Отображаем сообщение об успешном сохранении
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сделать скриншот: {e}")  # Обработка ошибок


def center_window(window, width, height):
    """Центрирование окна на экране."""
    screen_width = window.winfo_screenwidth()  # Получаем ширину экрана
    screen_height = window.winfo_screenheight()  # Получаем высоту экрана
    x = (screen_width - width) // 2  # Рассчитываем позицию окна по горизонтали
    y = (screen_height - height) // 2  # Рассчитываем позицию окна по вертикали
    window.geometry(f"{width}x{height}+{x}+{y}")  # Устанавливаем геометрию окна с центровкой
def show_settings():
    """Окно для настройки пути и формата сохранения."""
    settings_window = ttk.Notebook() # Создаем новое окно для настроек
    settings_window.title("Настройки")

    # Получаем текущие настройки из базы данных
    save_folder, file_format = get_settings()

    # Путь для сохранения
    def choose_folder():
        folder = filedialog.askdirectory(initialdir=SAVE_FOLDER)  # Открываем диалог выбора папки
        if folder:
            path_var.set(folder)

    path_var = tk.StringVar(value=save_folder)
    format_var = tk.StringVar(value=file_format)

    # UI элементы
    tk.Label(settings_window, text="Папка для сохранения скриншотов:").pack(pady=5)
    tk.Entry(settings_window, textvariable=path_var, width=50).pack(pady=5)
    tk.Button(settings_window, text="Выбрать папку", command=choose_folder).pack(pady=5)

    tk.Label(settings_window, text="Формат файла:").pack(pady=5)
    format_options = ["png", "jpg", "bmp", "gif"]
    tk.OptionMenu(settings_window, format_var, *format_options).pack(pady=5)

    # Сохранение настроек
    def save_settings():
        update_settings(path_var.get(), format_var.get())  # Обновляем настройки в базе данных
        settings_window.destroy()  # Закрываем окно настроек

    tk.Button(settings_window, text="Сохранить", command=save_settings).pack(pady=20)

    settings_window.mainloop()
# Функция для создания иконки в системном трее
def create_tray_icon(icon_event):
    # Создаём иконку для системного трея
    icon_image = Image.new('RGB', (64, 64), (255, 255, 255))  # Создаём пустое изображение
    draw = ImageDraw.Draw(icon_image)  # Рисуем на изображении
    draw.rectangle([16, 16, 48, 48], fill="blue")  # Рисуем синий прямоугольник

    # Создаем меню для иконки
    menu = Menu(MenuItem("О программе", show_about),
                MenuItem("Настройки", show_settings),  # Добавляем пункт настроек
                MenuItem("Выход", exit_program))  # Добавляем пункт выхода

    # Создаем иконку с меню
    icon = Icon("name", icon_image, menu=menu)

    # Устанавливаем флаг завершения программы
    icon_event.set()
    icon.run()  # Запускаем иконку в системном трее


def show_about(icon, item):
    """О программе"""
    messagebox.showinfo("О программе", "Программа для создания скриншотов с выбором области экрана.")  # Показываем информацию о программе

def exit_program(icon, item):
    """Выход из программы"""
    icon.stop()  # Останавливаем иконку в системном трее
    root.quit()  # Закрываем главное окно

# Создание главного окна
create_settings_db()
root = tk.Tk()
root.title("Скриншотер")  # Устанавливаем название окна

# Центрирование окна
window_width = 700  # Ширина окна
window_height = 200  # Высота окна
center_window(root, window_width, window_height)  # Центрируем окно на экране

# Метка с информацией о папке для сохранения скриншотов
#status_label = tk.Label(root, text=f"Скриншоты сохраняются в: {SAVE_FOLDER}", font=("Arial", 10))
#status_label.pack(pady=10)  # Добавляем метку в окно

# Кнопка для начала процесса создания скриншота
screenshot_button = tk.Button(root, text="Сделать скриншот", command=select_area, font=("Arial", 14))
screenshot_button.pack(pady=20)  # Добавляем кнопку в окно

# Флаг завершения программы
exit_flag = threading.Event()

# Запуск иконки в системном трее в отдельном потоке
tray_thread = threading.Thread(target=create_tray_icon, args=(exit_flag,), daemon=True)
tray_thread.start()  # Запускаем иконку в системном трее

root.iconbitmap("ico/favicon_.ico")
# Основной цикл Tkinter
root.mainloop()

# Завершение программы после закрытия окна
exit_flag.wait()  # Ожидаем сигнала для выхода
print("Программа завершена.")  # Выводим сообщение в консоль при завершении программы
