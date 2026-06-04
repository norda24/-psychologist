import tkinter as tk
from tkinter import messagebox, ttk
import re
import time
import os
import csv
from datetime import datetime

# --- КОНСТАНТЫ ДЛЯ СИСТЕМНЫХ ФАЙЛОВ ---
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")
THEME_FILE = "theme_config.txt"

# Создаем папку для логов, если её ещё нет (Пункт 1 усложнёнки)
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# --- РОЛЕВАЯ МОДЕЛЬ И ПОЛЬЗОВАТЕЛИ (Пункт 3 ТЗ) ---
ROLES = {1: "Администратор", 2: "Психолог (Пользователь)"}
USERS = [
    {"id": 1, "login": "admin", "password": "Password1!", "email": "head@psyhelp.com", "role_id": 1, "theme": "Light"},
    {"id": 2, "login": "psycho1", "password": "User123!", "email": "ivanov@psyhelp.com", "role_id": 2, "theme": "Light"}
]

# --- ТРИ ОСНОВНЫЕ СУЩНОСТИ ПРЕДМЕТНОЙ ОБЛАСТИ (Пункт 5 ТЗ) ---
# Сущность 1: Психологи центра
PSYCHOLOGISTS = [
    {"id": 1, "name": "Доктор Смирнова", "specialization": "Гештальт-терапия", "experience": 8},
    {"id": 2, "name": "Доктор Петров", "specialization": "КПТ (Когнитивная)", "experience": 12}
]

# Сущность 2: Клиенты, обратившиеся за помощью
CLIENTS = [
    {"id": 1, "name": "Алексей Иванов", "phone": "+79991112233", "age": 28},
    {"id": 2, "name": "Мария Сидорова", "phone": "+79994445566", "age": 34}
]

# Сущность 3: Консультации (Сессии)
SESSIONS = [
    {"id": 1, "psychologist_id": 1, "client_id": 1, "date": "2026-06-10", "status": "Запланировано"},
    {"id": 2, "psychologist_id": 2, "client_id": 2, "date": "2026-06-11", "status": "Завершено"}
]

# Глобальные переменные для отслеживания сессии и блокировок
CURRENT_USER = None
FAILED_ATTEMPTS = 0
LOCKOUT_UNTIL = 0
def log_action(action, result):
    """
    Запись логов в формате: [дата и время] [имя] [роль] [действие] [результат]
    Вызывается при любом ключевом событии в системе.
    """
    global CURRENT_USER
    if CURRENT_USER:
        user = CURRENT_USER["login"]
        role = ROLES[CURRENT_USER["role_id"]]
    else:
        user, role = "GUEST", "NONE"
        
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_str = f"[{dt}] [{user}] [{role}] [{action}] [{result}]\n"
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_str)

def load_theme_preference():
    """Загрузка сохраненной темы из файла (для сохранения между сессиями)"""
    if os.path.exists(THEME_FILE):
        with open(THEME_FILE, "r") as f:
            return f.read().strip()
    return "Light"

def save_theme_preference(theme_name):
    """Сохранение темы в файл конфигурации"""
    with open(THEME_FILE, "w") as f:
        f.write(theme_name)
class AuthFrame(tk.Frame):
    """Компонент интерфейса, отвечающий за экраны Входа и Регистрации"""
    def __init__(self, parent, on_login_success):
        super().__init__(parent, padx=20, pady=20)
        self.on_login_success = on_login_success
        self.build_login_screen()

    def build_login_screen(self):
        """Отрисовка формы входа"""
        for w in self.winfo_children(): w.destroy()
        
        tk.Label(self, text="Психологическая помощь — Вход", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(self, text="Логин:").grid(row=1, column=0, sticky="e", pady=5)
        l_entry = tk.Entry(self, width=25)
        l_entry.grid(row=1, column=1, pady=5)
        
        tk.Label(self, text="Пароль:").grid(row=2, column=0, sticky="e", pady=5)
        p_entry = tk.Entry(self, show="*", width=25)
        p_entry.grid(row=2, column=1, pady=5)
        
        def do_login():
            global FAILED_ATTEMPTS, LOCKOUT_UNTIL, CURRENT_USER
            # Проверяем таймер блокировки (Пункт 1 ТЗ)
            if time.time() < LOCKOUT_UNTIL:
                messagebox.showerror("Блокировка", f"Система заблокирована. Подождите {int(LOCKOUT_UNTIL - time.time())} сек.")
                return
            
            login, password = l_entry.get().strip(), p_entry.get()
            user = next((u for u in USERS if u["login"] == login and u["password"] == password), None)
            
            if user:
                FAILED_ATTEMPTS = 0
                CURRENT_USER = user
                log_action("LOGIN", "SUCCESS")
                self.on_login_success()
            else:
                FAILED_ATTEMPTS += 1
                log_action("LOGIN", f"FAILED_ATTEMPT_{FAILED_ATTEMPTS}")
                if FAILED_ATTEMPTS >= 3:
                    LOCKOUT_UNTIL = time.time() + 30
                    FAILED_ATTEMPTS = 0
                    messagebox.showerror("Блокировка", "Три неверные попытки! Вход заблокирован на 30 секунд.")
                else:
                    messagebox.showerror("Ошибка", f"Неверный логин или пароль. Осталось попыток: {3 - FAILED_ATTEMPTS}")

        tk.Button(self, text="Войти", command=do_login, bg="#4CAF50", fg="white").grid(row=3, column=1, pady=10, sticky="e")
        tk.Button(self, text="Регистрация терапевта", command=self.build_register_screen, bd=0, fg="blue", cursor="hand2").grid(row=4, column=0, columnspan=2)

    def build_register_screen(self):
        """Отрисовка формы регистрации новых пользователей"""
        for w in self.winfo_children(): w.destroy()
        
        labels = ["Логин:", "Пароль:", "Повтор пароля:", "Email:", "Специализация:"]
        entries = [tk.Entry(self, width=25, show="*" if i in (1,2) else "") for i in range(5)]
        
        for i, label in enumerate(labels):
            tk.Label(self, text=label).grid(row=i, column=0, sticky="e", pady=5)
            entries[i].grid(row=i, column=1, pady=5)
            
        def register():
            l, p, cp, em, sf = entries[0].get().strip(), entries[1].get(), entries[2].get(), entries[3].get().strip(), entries[4].get().strip()
            
            if not all([l, p, cp, em, sf]):
                messagebox.showerror("Ошибка", "Заполните все поля.")
                return
            if p != cp:
                messagebox.showerror("Ошибка", "Пароли не совпадают.")
                return
            # Валидация сложности пароля (Пункт 2 ТЗ)
            if len(p) < 8 or not re.search(r"\d", p) or not re.search(r"[A-Z]", p) or not re.search(r"[!@#$%]", p):
                messagebox.showerror("Ошибка", "Пароль слишком простой (нужна цифра, заглавная, спецсимвол).")
                return
            # Валидация формата почты через Regex
            if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", em):
                messagebox.showerror("Ошибка", "Неверный формат Email.")
                return
                
            # =========================================================================
            # Бизнес-правило из ТЗ: подстрока "admin" в любом регистре ПОСЛЕ собаки (@)
            # =========================================================================
            domain_part = em.split("@")[-1].lower()
            if "admin" in domain_part:
                messagebox.showerror("Ошибка", "Регистрация почтовых доменов, содержащих 'admin', запрещена!")
                return
                
            if any(u["login"] == l for u in USERS):
                messagebox.showerror("Ошибка", "Этот логин уже занят.")
                return
                
            USERS.append({"id": len(USERS)+1, "login": l, "password": p, "email": em, "role_id": 2, "theme": "Light"})
            log_action("REGISTER", f"USER_{l}_CREATED")
            messagebox.showinfo("Успех", "Регистрация успешна.")
            self.build_login_screen()

        tk.Button(self, text="Создать аккаунт", command=register, bg="#2196F3", fg="white").grid(row=5, column=1, pady=10, sticky="e")
        tk.Button(self, text="Назад", command=self.build_login_screen).grid(row=6, column=0, columnspan=2)
class MainApp(tk.Tk):
    """Основной класс графического интерфейса приложения"""
    def __init__(self):
        super().__init__()
        self.title("Центр психологической помощи — Практическая №5")
        self.geometry("850x600")
        self.current_theme = load_theme_preference()
        
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.show_auth()

    def apply_styles(self):
        """Динамическое применение цветов Тёмной / Светлой темы (Пункт 3 усложнёнки)"""
        bg = "#2d2d2d" if self.current_theme == "Dark" else "#f5f5f5"
        fg = "#ffffff" if self.current_theme == "Dark" else "#000000"
        self.configure(bg=bg)
        self.container.configure(bg=bg)
        
        style = ttk.Style()
        if self.current_theme == "Dark":
            style.theme_use('clam')
            style.configure("TNotebook", background=bg, foreground=fg)
            style.configure("TNotebook.Tab", background="#444444", foreground=fg)
            style.map("TNotebook.Tab", background=[("selected", "#555555")])
        else:
            style.theme_use('default')

    def show_auth(self):
        """Отображение экрана авторизации на старте"""
        for w in self.container.winfo_children(): w.destroy()
        self.apply_styles()
        auth = AuthFrame(self.container, on_login_success=self.show_main)
        auth.place(relx=0.5, rely=0.5, anchor="center")

    def show_main(self):
        """Отрисовка главной рабочей среды после успешного входа"""
        for w in self.container.winfo_children(): w.destroy()
        self.apply_styles()
        
        # Верхний тулбар (Header)
        header = tk.Frame(self.container, bg="#444444", pady=5)
        header.pack(fill="x", side="top")
        
        role_txt = ROLES[CURRENT_USER["role_id"]]
        tk.Label(header, text=f"Сотрудник: {CURRENT_USER['login']} ({role_txt})", fg="white", bg="#444444").pack(side="left", padx=10)
        
        def logout():
            global CURRENT_USER
            if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
                log_action("LOGOUT", "SUCCESS")
                CURRENT_USER = None
                self.show_auth()
        tk.Button(header, text="Выйти", command=logout, bg="#d9534f", fg="white").pack(side="right", padx=10)
        
        # Чекбокс Тёмной темы
        def toggle_theme():
            self.current_theme = "Dark" if theme_var.get() else "Light"
            CURRENT_USER["theme"] = self.current_theme
            save_theme_preference(self.current_theme)
            log_action("CHANGE_THEME", self.current_theme)
            self.show_main()

        theme_var = tk.BooleanVar(value=self.current_theme == "Dark")
        tk.Checkbutton(header, text="Тёмная тема", variable=theme_var, command=toggle_theme, bg="#444444", fg="white", selectcolor="#2d2d2d").pack(side="right", padx=20)

        # Контейнер вкладок
        notebook = ttk.Notebook(self.container)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Инициализируем таблицы сущностей
        self.build_crud_tab(notebook, "Психологи", PSYCHOLOGISTS, ["id", "name", "specialization", "experience"], "PSY")
        self.build_crud_tab(notebook, "Клиенты", CLIENTS, ["id", "name", "phone", "age"], "CLI")
        self.build_sessions_tab(notebook)
    def build_crud_tab(self, notebook, tab_title, dataset, columns, prefix):
        """Универсальный обработчик таблиц сущностей с кнопками управления"""
        tab_frame = tk.Frame(notebook)
        notebook.add(tab_frame, text=tab_title)
        
        tree = ttk.Treeview(tab_frame, columns=columns, show='headings', height=12)
        for col in columns:
            tree.heading(col, text=col.upper())
            tree.column(col, width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        def refresh():
            for r in tree.get_children(): tree.delete(r)
            for item in dataset: tree.insert("", tk.END, values=[item[c] for c in columns])
        refresh()

        btn_panel = tk.Frame(tab_frame)
        btn_panel.pack(fill="x", side="bottom", pady=5)

        def open_form(edit_item=None):
            """Окно добавления / редактирования записи"""
            form = tk.Toplevel(self)
            form.title("Карточка записи")
            form.geometry("320x280")
            
            # Метка для ошибок валидации на уникальность (Пункт 4 усложнёнки)
            err_lbl = tk.Label(form, text="", fg="red")
            err_lbl.pack(side="bottom", pady=5)
            
            ents = {}
            for col in columns[1:]:
                f = tk.Frame(form)
                f.pack(fill="x", padx=15, pady=3)
                tk.Label(f, text=f"{col}:", width=12, anchor="w").pack(side="left")
                e = tk.Entry(f)
                e.pack(side="right", fill="x", expand=True)
                if edit_item: e.insert(0, str(edit_item[col]))
                ents[col] = e
                
            def save():
                err_lbl.config(text="")
                # Валидация на пустоту и типы (Пункт 5 ТЗ)
                for col, entry in ents.items():
                    val = entry.get().strip()
                    if not val:
                        err_lbl.config(text="Заполните все поля!")
                        return
                    if col in ("age", "experience") and not val.isdigit():
                        err_lbl.config(text="Поле должно быть числовым!")
                        return
                    if col == "name" and len(val) < 3:
                        err_lbl.config(text="Имя должно быть от 3 символов!")
                        return

                # Проверка уникальности ключевого атрибута (Пункт 4 усложнёнки)
                key_val = ents["name"].get().strip()
                if any(str(x["name"]).lower() == key_val.lower() and (not edit_item or x["id"] != edit_item["id"]) for x in dataset):
                    err_lbl.config(text="Ошибка: Наименование уже существует!")
                    return

                if edit_item:
                    for col in columns[1:]:
                        val = ents[col].get().strip()
                        edit_item[col] = int(val) if col in ("age", "experience") else val
                    log_action(f"UPDATE_{prefix}", f"ID_{edit_item['id']}")
                else:
                    nid = max([x["id"] for x in dataset], default=0) + 1
                    nobj = {"id": nid}
                    for col in columns[1:]:
                        val = ents[col].get().strip()
                        nobj[col] = int(val) if col in ("age", "experience") else val
                    dataset.append(nobj)
                    log_action(f"CREATE_{prefix}", f"ID_{nid}")
                refresh()
                form.destroy()

            tk.Button(form, text="Сохранить", command=save, bg="green", fg="white").pack(pady=10)

        def delete():
            """Удаление с выводом точного сообщения из ТЗ (Пункт 5)"""
            if not tree.selection(): return
            item_id = int(tree.item(tree.selection())['values'][0])
            
            # Требование ТЗ к тексту диалогового окна
            msg = f"Вы действительно хотите удалить запись №{item_id}? Это действие нельзя отменить, и все ваши котики умрут от грусти."
            if messagebox.askyesno("Подтверждение", msg):
                dataset.remove(next(x for x in dataset if x["id"] == item_id))
                log_action(f"DELETE_{prefix}", f"ID_{item_id}")
                refresh()

        def export():
            """Выгрузка в CSV (Пункт 2 усложнёнки)"""
            fn = f"export_{prefix.lower()}s.csv"
            with open(fn, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(columns)
                for d in dataset: w.writerow([d[c] for c in columns])
            log_action(f"EXPORT_{prefix}", "SUCCESS")
            messagebox.showinfo("Экспорт", f"Выгружено в {fn}")

        # Разделение прав доступа ролевой модели
        if CURRENT_USER["role_id"] == 1: # Админ видит всё управление
            tk.Button(btn_panel, text="➕ Добавить", command=lambda: open_form(), bg="#5cb85c").pack(side="left", padx=5)
            tk.Button(btn_panel, text="✏️ Редактировать", command=lambda: open_form(next(x for x in dataset if x["id"] == int(tree.item(tree.selection())['values'][0]))) if tree.selection() else messagebox.showwarning("Внимание", "Выберите элемент"), bg="#f0ad4e").pack(side="left", padx=5)
            tk.Button(btn_panel, text="❌ Удалить", command=delete, bg="#d9534f", fg="white").pack(side="left", padx=5)
        
        tk.Button(btn_panel, text="💾 Экспорт CSV", command=export, bg="#5bc0de").pack(side="right", padx=5)

    def build_sessions_tab(self, notebook):
        """Сущность №3: Сессии консультаций (Фильтрация отображения данных по ролям)"""
        tab = tk.Frame(notebook)
        notebook.add(tab, text="Сессии консультаций")
        columns = ["id", "psychologist_id", "client_id", "date", "status"]
        
        tree = ttk.Treeview(tab, columns=columns, show='headings', height=12)
        for col in columns:
            tree.heading(col, text=col.upper())
            tree.column(col, width=110, anchor="center")
        tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Ролевая модель: обычный психолог видит только свои записи, Админ видит всё (Пункт 3 ТЗ)
        is_admin = CURRENT_USER["role_id"] == 1
        visible_data = SESSIONS if is_admin else [s for s in SESSIONS if s["psychologist_id"] == CURRENT_USER["id"]]
        
        for item in visible_data:
            tree.insert("", tk.END, values=[item[c] for c in columns])
            
        # Сводная статистика внизу экрана (Пункт 4 ТЗ)
        lbl_frame = tk.Frame(tab, bg="#dddddd", pady=5)
        lbl_frame.pack(fill="x", side="bottom")
        tk.Label(lbl_frame, text=f" Сводная статистика вкладок: Вам доступно сессий: {len(visible_data)} ", bg="#dddddd").pack(side="left")

# --- СТАРТ ПРИЛОЖЕНИЯ ---
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
