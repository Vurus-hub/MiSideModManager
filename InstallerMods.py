import os
import shutil
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import json
from datetime import datetime
import threading


class MiSideModInstaller:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("✨ MiSide Mod Manager ✨")
        self.window.geometry("900x650")
        self.window.minsize(800, 550)

        # Настройка цветовой схемы
        self.colors = {
            'bg': '#1a1a1a',
            'fg': '#ffffff',
            'accent': '#7aa2f7',
            'success': '#9ece6a',
            'warning': '#e0af68',
            'error': '#f7768e',
            'secondary': '#292e42',
        }

        self.window.configure(bg=self.colors['bg'])

        # Переменные
        self.game_path = tk.StringVar()
        self.mods = []
        self.auto_backup = tk.BooleanVar(value=True)

        # Создаем папки
        self.setup_folders()

        self.setup_ui()
        self.refresh_mods()

    def setup_folders(self):
        """Создание структуры папок"""
        self.base_folder = os.path.dirname(os.path.abspath(__file__))

        self.mods_folder = os.path.join(self.base_folder, "mods")
        self.backup_folder = os.path.join(self.base_folder, "backups")
        self.temp_folder = os.path.join(self.base_folder, "temp")
        self.logs_folder = os.path.join(self.base_folder, "logs")

        for folder in [self.mods_folder, self.backup_folder, self.temp_folder, self.logs_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)

    def find_game_mods_folder(self, game_path):
        """Поиск папки для модов в игре"""
        if not game_path or not os.path.exists(game_path):
            return None

        custom_path = os.path.join(game_path, "Data", "Custom")

        if not os.path.exists(custom_path):
            try:
                os.makedirs(custom_path)
                print(f"Создана папка: {custom_path}")
            except:
                pass

        if os.path.exists(custom_path):
            return custom_path

        return custom_path

    def find_game_exe(self, game_path):
        """Поиск исполняемого файла игры"""
        if not game_path or not os.path.exists(game_path):
            return None

        exe_path = os.path.join(game_path, "MiSideFull.exe")
        if os.path.exists(exe_path):
            return exe_path

        possible_exe = [
            os.path.join(game_path, "MiSide.exe"),
            os.path.join(game_path, "Miside.exe"),
            os.path.join(game_path, "MiSideFull.exe"),
        ]

        for exe in possible_exe:
            if os.path.exists(exe):
                return exe

        for file in os.listdir(game_path):
            if file.lower().endswith('.exe'):
                return os.path.join(game_path, file)

        return None

    def setup_ui(self):
        """Создание интерфейса"""
        main_frame = tk.Frame(self.window, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        title_label = tk.Label(
            main_frame,
            text="🎮 MISIDE MOD MANAGER",
            font=('Segoe UI', 24, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        title_label.pack(pady=(0, 20))

        self.status_frame = tk.Frame(main_frame, bg=self.colors['secondary'], height=40)
        self.status_frame.pack(fill=tk.X, pady=(0, 20))
        self.status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            self.status_frame,
            text="⚪ Не подключено к игре",
            font=('Segoe UI', 10),
            bg=self.colors['secondary'],
            fg=self.colors['fg']
        )
        self.status_label.pack(expand=True)

        path_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        path_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            path_frame,
            text="📁 Путь к игре:",
            font=('Segoe UI', 10),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.path_entry = tk.Entry(
            path_frame,
            textvariable=self.game_path,
            font=('Segoe UI', 10),
            bg=self.colors['secondary'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            relief='flat'
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        tk.Button(
            path_frame,
            text="Обзор",
            font=('Segoe UI', 10),
            bg=self.colors['accent'],
            fg='white',
            activebackground=self.colors['accent'],
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            command=self.browse_game
        ).pack(side=tk.LEFT)

        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(content_frame, bg=self.colors['secondary'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(
            left_frame,
            text="📦 Доступные моды",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['secondary'],
            fg=self.colors['fg']
        ).pack(pady=10)

        list_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.mod_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectbackground=self.colors['accent'],
            selectforeground='white',
            relief='flat',
            font=('Segoe UI', 10),
            height=15
        )
        self.mod_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.mod_listbox.yview)

        right_frame = tk.Frame(content_frame, bg=self.colors['secondary'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            right_frame,
            text="⚙️ Управление",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['secondary'],
            fg=self.colors['fg']
        ).pack(pady=10)

        info_frame = tk.Frame(right_frame, bg=self.colors['bg'])
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            info_frame,
            text="ℹ️ Информация о выбранном моде:",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(anchor=tk.W, pady=5)

        self.info_text = tk.Text(
            info_frame,
            height=6,
            bg=self.colors['secondary'],
            fg=self.colors['fg'],
            relief='flat',
            font=('Segoe UI', 9),
            wrap=tk.WORD
        )
        self.info_text.pack(fill=tk.X)

        settings_frame = tk.Frame(right_frame, bg=self.colors['bg'])
        settings_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            settings_frame,
            text="🔧 Настройки:",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(anchor=tk.W, pady=5)

        self.backup_check = tk.Checkbutton(
            settings_frame,
            text="Автоматически создавать бэкап",
            variable=self.auto_backup,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=self.colors['bg'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg'],
            font=('Segoe UI', 9)
        )
        self.backup_check.pack(anchor=tk.W)

        self.install_path_label = tk.Label(
            settings_frame,
            text="📂 Моды будут установлены в: Data/Custom/",
            font=('Segoe UI', 9),
            bg=self.colors['bg'],
            fg=self.colors['accent'],
            wraplength=250
        )
        self.install_path_label.pack(anchor=tk.W, pady=5)

        buttons_frame = tk.Frame(right_frame, bg=self.colors['bg'])
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)

        buttons = [
            ("🔄 Обновить список", self.refresh_mods, self.colors['secondary']),
            ("💾 Создать бэкап", self.create_backup, self.colors['warning']),
            ("📦 Установить выбранные", self.install_mods, self.colors['success']),
            ("🧹 Очистить временные", self.clean_temp, self.colors['error']),
        ]

        for text, command, color in buttons:
            btn = tk.Button(
                buttons_frame,
                text=text,
                font=('Segoe UI', 10),
                bg=color,
                fg='white',
                activebackground=color,
                activeforeground='white',
                relief='flat',
                cursor='hand2',
                command=command
            )
            btn.pack(fill=tk.X, pady=3)

        self.progress = ttk.Progressbar(
            right_frame,
            mode='indeterminate',
            style='Custom.Horizontal.TProgressbar'
        )
        self.progress.pack(fill=tk.X, padx=10, pady=10)

        log_frame = tk.Frame(right_frame, bg=self.colors['bg'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(
            log_frame,
            text="📋 Лог операций:",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(anchor=tk.W, pady=5)

        log_text_frame = tk.Frame(log_frame, bg=self.colors['bg'])
        log_text_frame.pack(fill=tk.BOTH, expand=True)

        log_scrollbar = tk.Scrollbar(log_text_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_text_frame,
            yscrollcommand=log_scrollbar.set,
            height=8,
            bg=self.colors['secondary'],
            fg=self.colors['fg'],
            relief='flat',
            font=('Segoe UI', 9),
            state=tk.DISABLED
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scrollbar.config(command=self.log_text.yview)

        # Привязываем события
        self.mod_listbox.bind('<<ListboxSelect>>', self.on_mod_select)
        # Используем правильный метод для отслеживания изменений
        self.game_path.trace_add('write', lambda *args: self.update_connection_status())

    def browse_game(self):
        """Выбор папки с игрой"""
        path = filedialog.askdirectory(title="Выберите папку с игрой MiSide")
        if path:
            self.game_path.set(path)
            self.update_connection_status()

    def update_connection_status(self, *args):
        """Обновление статуса подключения"""
        game_path = self.game_path.get()

        if not game_path:
            self.status_label.config(text="⚪ Не подключено к игре", fg=self.colors['fg'])
            return

        data_path = os.path.join(game_path, "Data")
        custom_path = os.path.join(data_path, "Custom")
        game_exe = self.find_game_exe(game_path)

        if os.path.exists(data_path) and game_exe:
            if not os.path.exists(custom_path):
                try:
                    os.makedirs(custom_path)
                    self.log(f"📁 Создана папка для модов: {custom_path}")
                except Exception as e:
                    self.log(f"⚠️ Не удалось создать папку Custom: {e}")

            self.status_label.config(
                text="✅ Подключено к игре",
                fg=self.colors['success']
            )
            self.log(f"✅ Найдена игра: {os.path.basename(game_exe)}")
            self.log(f"✅ Папка для модов: Data/Custom/")
        else:
            self.status_label.config(
                text="❌ Папка игры не найдена (нет Data/)",
                fg=self.colors['error']
            )

    def refresh_mods(self):
        """Обновление списка модов"""
        self.mod_listbox.delete(0, tk.END)
        self.mods = []

        if os.path.exists(self.mods_folder):
            for file in os.listdir(self.mods_folder):
                file_path = os.path.join(self.mods_folder, file)
                if os.path.isfile(file_path) or os.path.isdir(file_path):
                    self.mods.append(file)

                    if os.path.isdir(file_path):
                        icon = "📁"
                    elif file.endswith('.pak'):
                        icon = "📦"
                    elif file.endswith('.zip'):
                        icon = "🗜️"
                    elif file.endswith(('.png', '.jpg', '.jpeg')):
                        icon = "🖼️"
                    else:
                        icon = "📄"

                    self.mod_listbox.insert(tk.END, f"{icon} {file}")

            self.log(f"🔄 Найдено модов: {len(self.mods)}")

            game_path = self.game_path.get()
            if game_path:
                custom_path = os.path.join(game_path, "Data", "Custom")
                if os.path.exists(custom_path):
                    installed = [f for f in os.listdir(custom_path) if f.endswith(('.pak', '.png', '.jpg'))]
                    self.log(f"📊 Установлено модов в игре: {len(installed)}")

    def on_mod_select(self, event):
        """Обработка выбора мода"""
        selection = self.mod_listbox.curselection()
        if not selection:
            return

        mod_name = self.mods[selection[0]]
        mod_path = os.path.join(self.mods_folder, mod_name)

        info = f"📄 Имя: {mod_name}\n"

        if os.path.isdir(mod_path):
            info += "📁 Тип: Папка\n"
            files = os.listdir(mod_path)
            pak_files = [f for f in files if f.endswith('.pak')]
            img_files = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg'))]
            info += f"📦 Содержит: {len(pak_files)} .pak, {len(img_files)} изображений\n"
        else:
            size = os.path.getsize(mod_path)
            info += f"📦 Тип: {os.path.splitext(mod_name)[1]}\n"
            info += f"📊 Размер: {self.format_size(size)}\n"

        mod_time = datetime.fromtimestamp(os.path.getmtime(mod_path))
        info += f"⏰ Изменен: {mod_time.strftime('%d.%m.%Y %H:%M')}"
        info += f"\n\n📂 Будет установлено в:\nData/Custom/"

        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)

    def format_size(self, bytes):
        """Форматирование размера"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} ТБ"

    def create_backup(self):
        """Создание бэкапа папки Custom"""
        game_path = self.game_path.get()
        if not game_path:
            messagebox.showerror("Ошибка", "Сначала выберите папку с игрой!")
            return

        custom_path = os.path.join(game_path, "Data", "Custom")
        if not os.path.exists(custom_path):
            messagebox.showinfo("Информация", "Папка Custom пуста или не существует. Бэкап не требуется.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_folder, f"custom_backup_{timestamp}")
        os.makedirs(backup_path)

        try:
            copied = 0
            for file in os.listdir(custom_path):
                src = os.path.join(custom_path, file)
                dst = os.path.join(backup_path, file)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    copied += 1

            self.log(f"✅ Создан бэкап папки Custom: {copied} файлов")
            messagebox.showinfo("Успех", f"Бэкап создан!\nСкопировано файлов: {copied}")

        except Exception as e:
            self.log(f"❌ Ошибка создания бэкапа: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось создать бэкап:\n{str(e)}")

    def extract_zip_smart(self, zip_path, custom_folder):
        """Умная распаковка ZIP архива в папку Custom"""
        extracted = []

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            self.log(f"📦 Анализ ZIP: {len(file_list)} файлов")

            # Показываем содержимое архива
            if len(file_list) > 5:
                self.log(f"   Содержимое: {', '.join(file_list[:5])}...")
            else:
                self.log(f"   Содержимое: {', '.join(file_list)}")

            # Ищем файлы модов в любой папке
            mod_files = []
            for file in file_list:
                filename = os.path.basename(file)
                if filename and filename.endswith(('.pak', '.png', '.jpg', '.jpeg')):
                    mod_files.append(file)
                    self.log(f"   Найден файл мода: {file}")

            if not mod_files:
                self.log("⚠️ В архиве нет файлов модов (нужны .pak, .png, .jpg)")
                return extracted

            for mod_file in mod_files:
                try:
                    filename = os.path.basename(mod_file)
                    self.log(f"   Извлекаю: {filename}")

                    # Извлекаем во временную папку
                    temp_path = zip_ref.extract(mod_file, self.temp_folder)

                    # Копируем в папку Custom
                    dest_path = os.path.join(custom_folder, filename)

                    # Если файл существует, делаем бэкап
                    if os.path.exists(dest_path) and self.auto_backup.get():
                        backup_name = f"auto_backup_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        backup_path = os.path.join(self.backup_folder, backup_name)
                        shutil.move(dest_path, backup_path)
                        self.log(f"   💾 Создан бэкап: {filename}")

                    shutil.copy2(temp_path, dest_path)
                    extracted.append(filename)
                    self.log(f"   ✅ Установлен: {filename}")

                    # Удаляем временный файл
                    os.remove(temp_path)

                except Exception as e:
                    self.log(f"   ❌ Ошибка: {str(e)}")

            # Очищаем временные папки
            for item in os.listdir(self.temp_folder):
                item_path = os.path.join(self.temp_folder, item)
                if os.path.isdir(item_path):
                    try:
                        shutil.rmtree(item_path)
                    except:
                        pass

        return extracted

    def install_mods(self):
        """Установка выбранных модов"""
        selected = self.mod_listbox.curselection()

        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите моды для установки!")
            return

        game_path = self.game_path.get()
        if not game_path:
            messagebox.showerror("Ошибка", "Сначала выберите папку с игрой!")
            return

        custom_folder = os.path.join(game_path, "Data", "Custom")
        if not os.path.exists(custom_folder):
            try:
                os.makedirs(custom_folder)
                self.log(f"📁 Создана папка: {custom_folder}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать папку Custom:\n{str(e)}")
                return

        thread = threading.Thread(target=self._install_thread, args=(selected, custom_folder))
        thread.daemon = True
        thread.start()

    def _install_thread(self, selected, custom_folder):
        """Поток установки"""
        self.progress.start()

        installed = 0
        failed = 0

        for i in selected:
            mod_name = self.mods[i]
            mod_path = os.path.join(self.mods_folder, mod_name)

            self.log(f"📦 Установка: {mod_name}")

            try:
                if os.path.isdir(mod_path):
                    files_copied = 0
                    for file in os.listdir(mod_path):
                        file_path = os.path.join(mod_path, file)
                        if os.path.isfile(file_path) and file.endswith(('.pak', '.png', '.jpg', '.jpeg')):
                            dst = os.path.join(custom_folder, file)

                            if os.path.exists(dst) and self.auto_backup.get():
                                backup_name = f"auto_backup_{file}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                backup_path = os.path.join(self.backup_folder, backup_name)
                                shutil.move(dst, backup_path)

                            shutil.copy2(file_path, dst)
                            files_copied += 1
                            self.log(f"  ✅ {file}")

                    if files_copied > 0:
                        installed += 1
                    else:
                        self.log(f"  ⚠️ В папке нет файлов модов")
                        failed += 1

                elif mod_name.endswith('.zip'):
                    extracted = self.extract_zip_smart(mod_path, custom_folder)
                    if extracted:
                        installed += 1
                    else:
                        failed += 1

                elif mod_name.endswith(('.pak', '.png', '.jpg', '.jpeg')):
                    dst = os.path.join(custom_folder, mod_name)

                    if os.path.exists(dst) and self.auto_backup.get():
                        backup_name = f"auto_backup_{mod_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        backup_path = os.path.join(self.backup_folder, backup_name)
                        shutil.move(dst, backup_path)

                    shutil.copy2(mod_path, dst)
                    installed += 1
                    self.log(f"  ✅ {mod_name}")

                else:
                    self.log(f"  ⚠️ Неподдерживаемый формат: {mod_name}")
                    failed += 1

            except Exception as e:
                self.log(f"  ❌ Ошибка: {str(e)}")
                failed += 1

        self.progress.stop()
        self.clean_temp()

        self.window.after(0, lambda: messagebox.showinfo(
            "Установка завершена",
            f"✅ Успешно установлено модов: {installed}\n❌ Ошибок: {failed}\n\n📂 Все файлы скопированы в:\nData/Custom/"
        ))

        self.log(f"📊 Итог: {installed} установлено, {failed} ошибок")

        if os.path.exists(custom_folder):
            installed_files = [f for f in os.listdir(custom_folder) if f.endswith(('.pak', '.png', '.jpg', '.jpeg'))]
            self.log(f"📊 Всего в игре: {len(installed_files)} файлов модов")

    def clean_temp(self):
        """Очистка временных файлов"""
        if os.path.exists(self.temp_folder):
            try:
                for file in os.listdir(self.temp_folder):
                    file_path = os.path.join(self.temp_folder, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                self.log("🧹 Временные файлы очищены")
            except Exception as e:
                self.log(f"⚠️ Ошибка очистки: {str(e)}")

    def log(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        log_file = os.path.join(self.logs_folder, f"log_{datetime.now().strftime('%Y%m%d')}.txt")
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except:
            pass

    def run(self):
        """Запуск приложения"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

        self.window.mainloop()


if __name__ == "__main__":
    app = MiSideModInstaller()
    app.run()