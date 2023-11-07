import os
import tkinter as tk
from tkinter import filedialog
import logging
import configparser
from ttkbootstrap import Entry, Label, Button, Text, Style
from file_watcher_service import FileWatcherService

class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secware")
        self.root.iconbitmap('icon.ico')
        # Load the configuration settings
        self.config = configparser.ConfigParser()
        self.config_file = "config.ini"
        self.watch_folder = self.load_config()

        self.watch_folder_label = Label(root, text="Select folder to watch:")
        self.watch_folder_label.pack(pady=10)

        self.input_frame = tk.Frame(root)
        self.input_frame.pack()

        self.watch_folder_entry = Entry(self.input_frame)
        self.watch_folder_entry.pack(side="left", padx=10)

        self.browse_button = Button(self.input_frame, text="Select", command=self.browse_folder, style='primary.TButton')
        self.browse_button.pack(side="left")

        self.start_button = Button(root, text="Start Watching", command=self.start_watching, style='success.TButton')
        self.start_button.pack(pady=10)

        self.stop_button = Button(root, text="Stop Watching", command=self.stop_watching, style='danger.TButton', state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        self.log_text = Text(root, height=10, width=50)
        self.log_text.pack(pady=10)

        logging.basicConfig(filename="service.log", level=logging.INFO, format='%(asctime)s - %(message)s')

        self.file_watcher_service = None

        if self.watch_folder:
            self.watch_folder_entry.insert(0, self.watch_folder)

    def browse_folder(self):
        self.watch_folder = filedialog.askdirectory()
        self.watch_folder_entry.delete(0, tk.END)
        self.watch_folder_entry.insert(0, self.watch_folder)

    def start_watching(self):
        if not self.watch_folder:
            self.log("Please select a folder to watch before starting.")
            return

        # Save the selected folder to the configuration file
        self.save_config(self.watch_folder)

        if not self.file_watcher_service:
            self.file_watcher_service = FileWatcherService(self, self.watch_folder)
            self.file_watcher_service.start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log(f"Started watching for new .exe files in {self.watch_folder}.")

    def stop_watching(self):
        if self.file_watcher_service:
            self.file_watcher_service.stop()
            self.file_watcher_service.join()
            self.file_watcher_service = None
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.log("Stopped watching for new .exe files.")

    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            if self.config.has_section("Settings") and self.config.has_option("Settings", "WatchFolder"):
                return self.config.get("Settings", "WatchFolder")
        return ""

    def save_config(self, folder):
        self.config["Settings"] = {"WatchFolder": folder}
        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)

    def file_detected_callback(self, file_path):
        self.log(f"New .exe file detected: {file_path}")